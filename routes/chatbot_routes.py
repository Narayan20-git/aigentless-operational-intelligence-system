"""
chatbot_routes.py — FastAPI router for the ADK-powered AI chatbot endpoint.

Registered in main.py under the /api prefix.
Does NOT modify any existing route or service.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from config.database import db_is_ready, startup_database
from services.chatbot_service import OUT_OF_SCOPE_REPLY, run_chatbot


async def require_supabase(request: Request) -> None:
    if not getattr(request.app.state, "db_available", False):
        request.app.state.db_available = await startup_database()
    if not request.app.state.db_available and db_is_ready():
        request.app.state.db_available = True
    if not request.app.state.db_available:
        raise HTTPException(
            status_code=503,
            detail="Supabase unavailable. Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.",
        )


router = APIRouter(dependencies=[Depends(require_supabase)])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The user's message")
    session_id: str = Field(
        default="default",
        description="Unique session ID per user/tab for multi-turn memory",
    )
    user_id: str = Field(
        default="user",
        description="User identifier",
    )


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse, tags=["Chatbot"])
async def chat(req: ChatRequest) -> ChatResponse:
    """
    AI chatbot endpoint powered by Google ADK.

    Accepts the user message, session_id, and user_id.
    Returns a grounded response from live Supabase data.
    Out-of-scope questions return: "I don't have an answer to that."
    """
    reply = await run_chatbot(
        user_message=req.message,
        session_id=req.session_id,
        user_id=req.user_id,
    )
    return ChatResponse(reply=reply)
