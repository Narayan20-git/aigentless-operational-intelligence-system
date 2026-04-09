"""
Property Onboarding Router
Endpoints:
  GET  /onboarding                    → list all properties with onboarding status
  GET  /onboarding/summary            → KPI cards (ready/blocked/in-progress counts)
  GET  /onboarding/{property_id}      → property detail with all 6 section scores
  GET  /onboarding/{property_id}/sections → section breakdown
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.db import supabase

router = APIRouter()

# ── GET /onboarding/summary ─────────────────────────────────────────────────
@router.get("/onboarding/summary")
async def get_onboarding_summary(property_id: Optional[str] = Query(None)):
    """
    Powers the 4 KPI cards at the top of the screen:
    Ready to launch | In progress | Blocked | Avg. completeness
    Optional ?property_id filter for the dropdown
    """
    query = supabase.table("property_onboarding_status").select("*")
    if property_id:
        query = query.eq("property_id", property_id)

    res = query.execute()
    rows = res.data or []

    ready       = sum(1 for r in rows if r["status"] == "ready")
    in_progress = sum(1 for r in rows if r["status"] == "in-progress")
    blocked     = sum(1 for r in rows if r["status"] == "blocked")
    avg_pct     = round(sum(r["overall_completeness"] for r in rows) / len(rows)) if rows else 0

    return {
        "ready_to_launch":    ready,
        "in_progress":        in_progress,
        "blocked":            blocked,
        "avg_completeness":   avg_pct,
        "total_properties":   len(rows),
    }

# ── GET /onboarding ──────────────────────────────────────────────────────────
@router.get("/onboarding")
async def list_onboarding_properties(
    property_id: Optional[str] = Query(None),
    status:      Optional[str] = Query(None),
):
    """
    Powers the left panel properties list.
    Returns all properties with their onboarding status + active blockers.
    Optional filters: ?property_id= or ?status=blocked|in-progress|ready
    """
    # Get properties
    prop_query = supabase.table("properties").select(
        "id, name, description, units, go_live_date"
    )
    if property_id:
        prop_query = prop_query.eq("id", property_id)
    props = prop_query.execute().data or []

    # Get onboarding status
    status_query = supabase.table("property_onboarding_status").select("*")
    if property_id:
        status_query = status_query.eq("property_id", property_id)
    if status:
        status_query = status_query.eq("status", status)
    statuses = {r["property_id"]: r for r in (status_query.execute().data or [])}

    # Get unresolved blockers
    blockers_res = supabase.table("property_onboarding_blockers") \
        .select("property_id, message, severity") \
        .eq("resolved", False) \
        .execute()
    blockers_map: dict = {}
    for b in (blockers_res.data or []):
        blockers_map.setdefault(b["property_id"], []).append(b["message"])

    # Build response
    result = []
    for p in props:
        pid = p["id"]
        st  = statuses.get(pid, {})
        if status and st.get("status") != status:
            continue
        result.append({
            "property_id":          pid,
            "name":                 p["name"],
            "status":               st.get("status", "in-progress"),
            "overall_completeness": st.get("overall_completeness", 0),
            "blockers":             blockers_map.get(pid, []),
            "last_updated":         p.get("updated_at"),
            "go_live_date":         p.get("go_live_date"),
        })

    return {"properties": result, "total": len(result)}

# ── GET /onboarding/{property_id} ────────────────────────────────────────────
@router.get("/onboarding/{property_id}")
async def get_onboarding_detail(property_id: str):
    """
    Powers the right panel when a property is selected.
    Returns property detail + all 6 section scores + blockers.
    """
    # Property info
    prop_res = supabase.table("properties") \
        .select("id, name, description, units, year_built, website, amenities, go_live_date") \
        .eq("id", property_id) \
        .single() \
        .execute()

    if not prop_res.data:
        raise HTTPException(status_code=404, detail="Property not found")
    prop = prop_res.data

    # Onboarding status
    status_res = supabase.table("property_onboarding_status") \
        .select("*") \
        .eq("property_id", property_id) \
        .single() \
        .execute()
    status = status_res.data or {}

    # All 6 sections
    sections_res = supabase.table("property_onboarding_sections") \
        .select("section, completion_pct, status, metadata, updated_at") \
        .eq("property_id", property_id) \
        .execute()
    sections = {s["section"]: s for s in (sections_res.data or [])}

    # Active blockers
    blockers_res = supabase.table("property_onboarding_blockers") \
        .select("section, severity, message, description, action, ai_can_fix") \
        .eq("property_id", property_id) \
        .eq("resolved", False) \
        .execute()
    blockers = blockers_res.data or []

    return {
        "property": {
            "id":          prop["id"],
            "name":        prop["name"],
            "description": prop["description"],
            "units":       prop["units"],
            "year_built":  prop["year_built"],
            "website":     prop["website"],
        },
        "onboarding": {
            "overall_completeness": status.get("overall_completeness", 0),
            "status":               status.get("status", "in-progress"),
            "last_calculated_at":   status.get("last_calculated_at"),
        },
        "sections": {
            "property_info":     _section(sections, "property_info"),
            "units_floor_plans": _section(sections, "units_floor_plans"),
            "amenities":         _section(sections, "amenities"),
            "media_photos":      _section(sections, "media_photos"),
            "content_faqs":      _section(sections, "content_faqs"),
            "integrations":      _section(sections, "integrations"),
        },
        "blockers": blockers,
    }

def _section(sections: dict, key: str) -> dict:
    s = sections.get(key, {})
    return {
        "completion_pct": s.get("completion_pct", 0),
        "status":         s.get("status", "not-started"),
        "metadata":       s.get("metadata", {}),
    }
