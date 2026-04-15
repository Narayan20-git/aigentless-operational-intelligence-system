from fastapi import APIRouter, Depends, HTTPException, Query, Request

from config.database import db_is_ready, startup_database
from services.dashboard_service import (
    get_brief_objection_detail_payload,
    get_home_payload,
    get_home_ui_copy_payload,
    get_header_payload,
    get_integrations_payload,
    get_inventory_payload,
    get_inventory_unit_detail_payload,
    get_leads_summary_payload,
    get_navigation_payload,
    get_portfolio_overview_payload,
    get_profile_payload,
    get_property_onboarding_payload,
    get_property_options_payload,
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


@router.get("/properties/options")
async def properties_options():
    return await get_property_options_payload()


@router.get("/dashboard/home")
async def dashboard_home(
    property_id: str | None = Query(None, description="Filter widgets to this property UUID"),
    days: int = Query(7, description="Rolling window in days (7, 30, or 90)"),
    enrich_leads: bool = Query(
        True,
        description="If false, skip OpenAI on lead cards (faster load; heuristic copy only).",
    ),
):
    return await get_home_payload(property_id=property_id, days=days, enrich_leads=enrich_leads)


@router.get("/leads/summary")
async def leads_summary(
    property_id: str | None = Query(None),
    days: int = Query(7),
    enrich: bool = Query(
        True,
        description="If false, skip OpenAI enrichment (faster; heuristic objections/alternates/draft).",
    ),
):
    return await get_leads_summary_payload(
        property_id=property_id, days=days, enrich_with_llm=enrich
    )


@router.get("/inventory/vacant-units")
async def inventory_vacant_units(
    property_id: str | None = Query(None),
    days: int = Query(7),
):
    return await get_inventory_payload(property_id=property_id, days=days)


@router.get("/inventory/vacant-units/{unit_id}/detail")
async def inventory_vacant_unit_detail(unit_id: str):
    data = await get_inventory_unit_detail_payload(unit_id)
    if not data:
        raise HTTPException(status_code=404, detail="Unit not found")
    return data


@router.get("/properties/onboarding")
async def properties_onboarding(
    property_id: str | None = Query(None),
    days: int = Query(7),
):
    return await get_property_onboarding_payload(property_id=property_id, days=days)


@router.get("/portfolio/overview")
async def portfolio_overview(
    property_id: str | None = Query(None),
    days: int = Query(7),
    enrich_recommendations: bool = Query(
        True,
        description="If false, skip LLM recommendations and use DB-based fallback recommendations.",
    ),
):
    return await get_portfolio_overview_payload(
        property_id=property_id, days=days, enrich_recommendations=enrich_recommendations
    )


@router.get("/briefs/weekly")
async def briefs_weekly(
    property_id: str | None = Query(None, description="Scope snapshot to this property UUID"),
    days: int = Query(7, description="Rolling window in days (7, 30, or 90)"),
    start_date: str | None = Query(
        None, description="Optional custom range start date (YYYY-MM-DD)"
    ),
    end_date: str | None = Query(
        None, description="Optional custom range end date (YYYY-MM-DD)"
    ),
    enrich: bool = Query(
        True,
        description="If false, return rule-based brief only (no OpenAI; faster).",
    ),
):
    return await get_weekly_brief_payload(
        property_id=property_id,
        days=days,
        start_date=start_date,
        end_date=end_date,
        use_llm=enrich,
    )


@router.get("/briefs/objection-detail")
async def brief_objection_detail(
    topic: str = Query(..., description="Objection topic label"),
    property_id: str | None = Query(None, description="Scope snapshot to this property UUID"),
    days: int = Query(7, description="Rolling window in days"),
    start_date: str | None = Query(
        None, description="Optional custom range start date (YYYY-MM-DD)"
    ),
    end_date: str | None = Query(
        None, description="Optional custom range end date (YYYY-MM-DD)"
    ),
):
    return await get_brief_objection_detail_payload(
        topic=topic,
        property_id=property_id,
        days=days,
        start_date=start_date,
        end_date=end_date,
    )


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


@router.get("/ui/home-copy")
async def ui_home_copy():
    """Template copy + empty home shell for client fallback (DB + JSON merge)."""
    return await get_home_ui_copy_payload()
