from fastapi import APIRouter, Depends, HTTPException, Request

from config.database import db_is_ready, startup_database
from services.dashboard_service import (
    get_home_payload,
    get_header_payload,
    get_integrations_payload,
    get_inventory_payload,
    get_leads_summary_payload,
    get_navigation_payload,
    get_portfolio_overview_payload,
    get_profile_payload,
    get_property_onboarding_payload,
    get_weekly_brief_payload,
)


async def require_supabase(request: Request) -> None:
    # If startup check was stale/false, retry once on request.
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


@router.get("/dashboard/home")
async def dashboard_home():
    return await get_home_payload()


@router.get("/leads/summary")
async def leads_summary():
    return await get_leads_summary_payload()


@router.get("/inventory/vacant-units")
async def inventory_vacant_units():
    return await get_inventory_payload()


@router.get("/properties/onboarding")
async def properties_onboarding():
    return await get_property_onboarding_payload()


@router.get("/portfolio/overview")
async def portfolio_overview():
    return await get_portfolio_overview_payload()


@router.get("/briefs/weekly")
async def briefs_weekly():
    return await get_weekly_brief_payload()


@router.get("/integrations")
async def integrations():
    return await get_integrations_payload()


@router.get("/profile/summary")
async def profile_summary():
    return await get_profile_payload()


@router.get("/ui/header")
async def ui_header():
    return await get_header_payload()


@router.get("/ui/navigation")
async def ui_navigation():
    return await get_navigation_payload()
