"""
chatbot_service.py — Google ADK + OpenAI (gpt-4.1-mini) chatbot for Aigentless.

Architecture:
  - Google ADK (LlmAgent + Runner + InMemorySessionService) handles the agent loop
  - LiteLlm bridges ADK to OpenAI's gpt-4.1-mini
  - FunctionTool wraps each Supabase query function
  - OPENAI_API_KEY is read from .env

Design principles:
  - All answers strictly from live Supabase data via tools (no hallucination)
  - No hardcoded data whatsoever
  - Out-of-scope questions return "I don't have an answer to that."
  - Does not modify any existing service or route
"""
from __future__ import annotations

import logging
import os

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
MODEL = "openai/gpt-4.1-mini"  # LiteLlm prefix "openai/" routes to OpenAI API

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
# ADK setup — built once, reused across all requests
# ─────────────────────────────────────────────────────────────────────────────

_session_service: InMemorySessionService | None = None
_runner: Runner | None = None


def _get_openai_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your .env file.\n"
            "Get your key at: https://platform.openai.com/api-keys"
        )
    return key


def _get_runner() -> tuple[Runner, InMemorySessionService]:
    """Return cached runner or build it once on first call."""
    global _runner, _session_service

    if _runner is not None and _session_service is not None:
        return _runner, _session_service

    # Set API key for LiteLlm (reads OPENAI_API_KEY from environment)
    os.environ["OPENAI_API_KEY"] = _get_openai_api_key()

    logger.info("[Chatbot] Building ADK runner with model: %s", MODEL)

    adk_tools = [FunctionTool(fn) for fn in ALL_TOOL_FUNCTIONS]

    agent = LlmAgent(
        name="aigentless_assistant",
        model=LiteLlm(model=MODEL),
        instruction=_SYSTEM_PROMPT,
        tools=adk_tools,
    )

    _session_service = InMemorySessionService()

    _runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=_session_service,
    )

    logger.info("[Chatbot] Runner ready — model: %s", MODEL)
    return _runner, _session_service


def _reset_runner() -> None:
    """Reset runner on error so it rebuilds on next request."""
    global _runner, _session_service
    _runner = None
    _session_service = None


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

async def run_chatbot(
    user_message: str,
    session_id: str = "default",
    user_id: str = "user",
) -> str:
    """
    Run a single chatbot turn using Google ADK with OpenAI gpt-4.1-mini.

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
        logger.error("[Chatbot] %s", e)
        return OUT_OF_SCOPE_REPLY

    try:
        runner, session_svc = _get_runner()

        # Create session if it doesn't exist (all session methods are async)
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
            logger.info("[Chatbot] Created session %s for user %s", session_id, user_id)

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
            logger.info("[Chatbot] Reply generated successfully")
            return reply

        logger.warning("[Chatbot] Empty reply from agent")
        return OUT_OF_SCOPE_REPLY

    except Exception as exc:
        err_str = str(exc)

        if "429" in err_str or "rate_limit" in err_str.lower():
            logger.warning("[Chatbot] Rate limit hit: %s", err_str[:150])
            return "Too many requests. Please wait a moment and try again."

        if "insufficient_quota" in err_str.lower() or "quota" in err_str.lower():
            logger.error("[Chatbot] OpenAI quota exceeded: %s", err_str[:150])
            return (
                "OpenAI API quota exceeded. "
                "Please check https://platform.openai.com/usage"
            )

        if "401" in err_str or "invalid_api_key" in err_str.lower():
            logger.error("[Chatbot] Invalid OpenAI API key")
            _reset_runner()
            return "Invalid API key. Please check OPENAI_API_KEY in your .env file."

        if "503" in err_str or "502" in err_str:
            logger.warning("[Chatbot] OpenAI service temporarily unavailable")
            _reset_runner()
            return "OpenAI service is temporarily unavailable. Please try again shortly."

        logger.exception("[Chatbot] Unexpected error: %s", exc)
        return OUT_OF_SCOPE_REPLY
