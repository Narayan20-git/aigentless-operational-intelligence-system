"""
chatbot_service.py — Google ADK + OpenAI powered chatbot for Aigentless dashboard.

Architecture:
  - Google ADK (LlmAgent + Runner + InMemorySessionService) handles the agent loop
  - LiteLlm bridges ADK to OpenAI models (gpt-4.1-mini etc.)
  - FunctionTool wraps each Supabase query function
  - OPENAI_API_KEY is read from environment

Design principles:
  - All answers strictly from live Supabase data via tools (no hallucination)
  - No hardcoded data whatsoever
  - Out-of-scope questions return "I don't have an answer to that."
  - Does not modify any existing service or route
"""
from __future__ import annotations

import logging
import os
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
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

# ADK uses LiteLlm prefix "openai/" to route to OpenAI API
# Model preference — first supported model wins
_MODEL_PREFERENCE = [
    "openai/gpt-4.1-mini",
    "openai/gpt-4o-mini",
    "openai/gpt-4.1",
    "openai/gpt-4o",
]

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

## Out of scope — reply "I don't have an answer to that."
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


def _get_openai_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your .env file.\n"
            "Get your key at: https://platform.openai.com/api-keys"
        )
    return key


def _build_runner(model_name: str) -> tuple[Runner, InMemorySessionService]:
    """Build ADK Runner using LiteLlm to connect to OpenAI."""

    # LiteLlm reads OPENAI_API_KEY from environment automatically
    os.environ["OPENAI_API_KEY"] = _get_openai_api_key()

    # Wrap each Supabase tool with ADK FunctionTool
    adk_tools = [FunctionTool(fn) for fn in ALL_TOOL_FUNCTIONS]

    # LiteLlm bridges ADK → OpenAI. Model string must have "openai/" prefix.
    llm = LiteLlm(model=model_name)

    agent = LlmAgent(
        name="aigentless_assistant",
        model=llm,
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
    """Return cached runner or build a new one."""
    global _runner, _session_service, _current_model

    if _runner is not None and _session_service is not None:
        return _runner, _session_service

    last_error: Exception | None = None
    for model_name in _MODEL_PREFERENCE:
        try:
            logger.info("[Chatbot ADK+OpenAI] Building runner with model: %s", model_name)
            runner, session_svc = _build_runner(model_name)
            _runner = runner
            _session_service = session_svc
            _current_model = model_name
            logger.info("[Chatbot ADK+OpenAI] Runner ready with model: %s", model_name)
            return _runner, _session_service
        except Exception as e:
            logger.warning(
                "[Chatbot ADK+OpenAI] Model %s failed to init: %s", model_name, e
            )
            last_error = e
            continue

    raise RuntimeError(
        f"Could not initialise ADK+OpenAI runner. Last error: {last_error}"
    )


def _reset_runner() -> None:
    """Clear cached runner — next call will rebuild with next model."""
    global _runner, _session_service, _current_model
    _runner = None
    _session_service = None
    _current_model = None


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

async def run_chatbot(
    user_message: str,
    session_id: str = "default",
    user_id: str = "user",
) -> str:
    """
    Run a single chatbot turn using Google ADK with OpenAI backend.

    Args:
        user_message: The user's message.
        session_id:   Unique session ID per user/tab for multi-turn memory.
        user_id:      User identifier.

    Returns:
        Assistant reply string.
    """
    try:
        _get_openai_api_key()
    except RuntimeError as e:
        logger.error("[Chatbot ADK+OpenAI] %s", e)
        return OUT_OF_SCOPE_REPLY

    for attempt in range(2):
        try:
            runner, session_svc = _get_runner()

            # Ensure session exists — all session methods are async
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
                    "[Chatbot ADK+OpenAI] Created session %s for user %s",
                    session_id, user_id,
                )

            new_message = genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=user_message)],
            )

            # Run the ADK agent loop and collect final response
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
                    "[Chatbot ADK+OpenAI] Reply generated (model: %s)",
                    _current_model,
                )
                return reply

            logger.warning("[Chatbot ADK+OpenAI] Empty reply from agent")
            return OUT_OF_SCOPE_REPLY

        except Exception as exc:
            err_str = str(exc)

            is_quota = (
                "429" in err_str
                or "quota" in err_str.lower()
                or "rate_limit" in err_str.lower()
                or "insufficient_quota" in err_str.lower()
            )
            is_model = (
                "404" in err_str
                or "model_not_found" in err_str.lower()
                or "does not exist" in err_str.lower()
                or "not supported" in err_str.lower()
            )
            is_server = (
                "503" in err_str
                or "502" in err_str
                or "unavailable" in err_str.lower()
            )

            if (is_model or is_server) and attempt == 0:
                logger.warning(
                    "[Chatbot ADK+OpenAI] Resetting runner: %s", err_str[:150]
                )
                _reset_runner()
                continue

            if is_quota:
                logger.error(
                    "[Chatbot ADK+OpenAI] OpenAI quota/rate limit: %s", err_str[:150]
                )
                return (
                    "OpenAI API quota or rate limit reached. "
                    "Please check https://platform.openai.com/usage or try again shortly."
                )

            logger.exception("[Chatbot ADK+OpenAI] Unexpected error: %s", exc)
            return OUT_OF_SCOPE_REPLY

    return OUT_OF_SCOPE_REPLY
