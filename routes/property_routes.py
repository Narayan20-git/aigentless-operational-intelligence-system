from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from config.database import db_is_ready, startup_database
from services.property_service import list_properties


async def require_supabase(request: Request) -> None:
    if not getattr(request.app.state, "db_available", False):
        request.app.state.db_available = await startup_database()
    if not request.app.state.db_available and db_is_ready():
        request.app.state.db_available = True
    if not request.app.state.db_available:
        raise HTTPException(
            status_code=503,
            detail="Supabase unavailable. Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY/SUPABASE_KEY.",
        )


router = APIRouter(dependencies=[Depends(require_supabase)])


@router.get("/", response_model=list[dict[str, Any]])
async def list_all():
    return await list_properties()
