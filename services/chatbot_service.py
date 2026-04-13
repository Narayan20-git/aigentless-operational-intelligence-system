"""
chatbot_service.py — Google ADK-powered chatbot for the Aigentless dashboard.

Handles:
- gemini-2.5-flash (your POC project model)
- 503 UNAVAILABLE: retries with delay (model overloaded, temporary)
- 429 QUOTA: user-friendly message
- Async session management via InMemorySessionService
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types as genai_types

from services.chatbot_tools import ALL_TOOL_FUNCTIONS

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

OUT_OF_SCOPE_REPLY = "I don't have an answer to that."
APP_NAME = "aigentless_chatbot"

# Use gemini-2.5-flash first — matches your POC Project quota
# NOTE: "Default value is not supported" warnings are harmless — ignore them
_MODEL_PREFERENCE = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
]

# 503 retry config — model temporarily overloaded
_MAX_503_RETRIES = 3
_503_RETRY_DELAY_SECONDS = 5

_SYSTEM_PROMPT = """You are the AI Assistant embedded in the Aigentless property management dashboard.

## Your only job
Answer questions about the user's property portfolio using LIVE DATA from the provided tools.
Every number, unit name, and property name in your answer MUST come from a tool call result.

## Strict rules
1. NEVER invent, estimate, or assume any data. If you cannot answer using the tools, reply exactly:
   "I don't have an answer to that."
2. NEVER answer questions unrelated to property management (weather, coding, general knowledge etc).
   Reply exactly: "I don't have an answer to that."
3. Always call the most relevant tool before answering. Do not answer from memory.
4. If a tool returns 0 results, say so clearly — do not fabricate alternatives.
5. Be concise. Lead with the key number or insight, then list details.
6. Do not mention tool names in your reply. Speak naturally as an assistant.
7. Format unit lists with bullet points.

## What you can answer
- Vacant units (filter by days vacant, property name)
- At-risk or stale units
- Occupancy rates and property summary
- Recent tour bookings
- Lead and prospect pipeline stats

## What is out of scope — reply "I don't have an answer to that."
- Financial projections, rent predictions, investment advice
- Maintenance, staff, leases, payments
- General knowledge, weather, coding
- Anything not answerable by the available tools
"""

# ─────────────────────────────────────────────────────────────────────────────
# ADK setup — built once, reused across requests
# ─────────────────────────────────────────────────────────────────────────────

_session_service: InMemorySessionService | None = None
_runner: Runner | None = None
_current_model: str | None = None


def _get_google_api_key() -> str:
    key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GOOGLE_API_KEY is not set in .env file.")
    return key


def _build_runner(model_name: str) -> tuple[Runner, InMemorySessionService]:
    os.environ["GOOGLE_API_KEY"] = _get_google_api_key()
    adk_tools = [FunctionTool(fn) for fn in ALL_TOOL_FUNCTIONS]
    agent = LlmAgent(
        name="aigentless_assistant",
        model=model_name,
        instruction=_SYSTEM_PROMPT,
        tools=adk_tools,
    )
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service,
    )
    return runner, session_service


def _get_runner() -> tuple[Runner, InMemorySessionService]:
    global _runner, _session_service, _current_model
    if _runner is not None and _session_service is not None:
        return _runner, _session_service

    last_error: Exception | None = None
    for model_name in _MODEL_PREFERENCE:
        try:
            logger.info("[Chatbot ADK] Building runner with model: %s", model_name)
            runner, session_svc = _build_runner(model_name)
            _runner = runner
            _session_service = session_svc
            _current_model = model_name
            logger.info("[Chatbot ADK] Runner ready with model: %s", model_name)
            return _runner, _session_service
        except Exception as e:
            logger.warning("[Chatbot ADK] Model %s failed to init: %s", model_name, e)
            last_error = e
            continue

    raise RuntimeError(f"Could not init ADK runner. Last error: {last_error}")


def _reset_runner() -> None:
    global _runner, _session_service, _current_model
    _runner = None
    _session_service = None
    _current_model = None


def _is_quota_error(err_str: str) -> bool:
    return (
        "429" in err_str
        or "quota" in err_str.lower()
        or "resource_exhausted" in err_str.lower()
    )


def _is_model_error(err_str: str) -> bool:
    return (
        "404" in err_str
        or "not found for api" in err_str.lower()
        or "not supported for generatecontent" in err_str.lower()
        or "deprecated" in err_str.lower()
    )


def _is_server_error(err_str: str) -> bool:
    """503 = model temporarily overloaded — retry after delay."""
    return (
        "503" in err_str
        or "unavailable" in err_str.lower()
        or "high demand" in err_str.lower()
        or "temporarily" in err_str.lower()
    )


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

async def run_chatbot(
    user_message: str,
    session_id: str = "default",
    user_id: str = "user",
) -> str:
    """
    Run a single chatbot turn using Google ADK.

    Args:
        user_message: The user's message.
        session_id:   Unique session ID per user/tab for multi-turn memory.
        user_id:      User identifier.

    Returns:
        Assistant reply string.
    """
    try:
        _get_google_api_key()
    except RuntimeError as e:
        logger.error("[Chatbot ADK] %s", e)
        return OUT_OF_SCOPE_REPLY

    # Outer loop: try current model, then reset and try next on model/quota errors
    for attempt in range(2):
        try:
            runner, session_svc = _get_runner()

            # Ensure session exists (all session methods are async)
            existing = await session_svc.get_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id,
            )
            if existing is None:
                await session_svc.create_session(
                    app_name=APP_NAME,
                    user_id=user_id,
                    session_id=session_id,
                )
                logger.info(
                    "[Chatbot ADK] Created session %s for user %s",
                    session_id, user_id,
                )

            new_message = genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=user_message)],
            )

            # Inner loop: retry on 503 (model overloaded) with delay
            last_exc: Exception | None = None
            for retry in range(_MAX_503_RETRIES):
                try:
                    reply_parts: list[str] = []
                    async for event in runner.run_async(
                        user_id=user_id,
                        session_id=session_id,
                        new_message=new_message,
                    ):
                        if event.is_final_response():
                            if event.content and event.content.parts:
                                for part in event.content.parts:
                                    if part.text:
                                        reply_parts.append(part.text)

                    reply = " ".join(reply_parts).strip()
                    if reply:
                        logger.info(
                            "[Chatbot ADK] Reply generated (model: %s)",
                            _current_model,
                        )
                        return reply

                    logger.warning("[Chatbot ADK] Empty reply from agent")
                    return OUT_OF_SCOPE_REPLY

                except Exception as inner_exc:
                    inner_str = str(inner_exc)
                    if _is_server_error(inner_str):
                        wait = _503_RETRY_DELAY_SECONDS * (retry + 1)
                        logger.warning(
                            "[Chatbot ADK] 503 model overloaded (retry %d/%d), "
                            "waiting %ds...",
                            retry + 1, _MAX_503_RETRIES, wait,
                        )
                        await asyncio.sleep(wait)
                        last_exc = inner_exc
                        continue
                    # Not a 503 — re-raise for outer handler
                    raise inner_exc

            # All 503 retries exhausted
            logger.error(
                "[Chatbot ADK] Model still unavailable after %d retries",
                _MAX_503_RETRIES,
            )
            return (
                "The AI model is currently experiencing high demand. "
                "Please try again in a few seconds."
            )

        except Exception as exc:
            err_str = str(exc)

            if _is_quota_error(err_str):
                logger.error(
                    "[Chatbot ADK] Quota exhausted for model %s. "
                    "Check https://aistudio.google.com/app/apikey",
                    _current_model,
                )
                if attempt == 0:
                    _reset_runner()
                    continue
                return (
                    "API quota limit reached. "
                    "Please check your Google AI Studio quota or try again later."
                )

            if _is_model_error(err_str) and attempt == 0:
                logger.warning(
                    "[Chatbot ADK] Model error, trying next model: %s",
                    err_str[:150],
                )
                _reset_runner()
                continue

            logger.exception("[Chatbot ADK] Unexpected error: %s", exc)
            return OUT_OF_SCOPE_REPLY

    return OUT_OF_SCOPE_REPLY
