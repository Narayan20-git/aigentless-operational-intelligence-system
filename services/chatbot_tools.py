"""
chatbot_tools.py — Supabase query functions for Google ADK FunctionTool.

IMPORTANT: ADK's automatic function calling does NOT support:
  - Optional[X] or X | None type hints
  - Union types
All optional parameters must use plain types with default values only.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta, date
from typing import Any

from config.database import get_client
from services.dashboard_service import (
    _chunks,
    _days_vacant,
    _parse_ts,
    _space_is_vacant_for_inventory,
    normalize_dashboard_days,
)


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 1 — Vacant units
# ─────────────────────────────────────────────────────────────────────────────

def _get_vacant_units_sync(
    days_vacant_min: int = 0,
    property_name: str = "",
) -> dict[str, Any]:
    client = get_client()
    sp = (
        client.table("spaces")
        .select("unit_id,available_date,availability_status,created_at")
        .limit(400)
        .execute()
    )
    spaces_list = [
        s for s in (sp.data or [])
        if _space_is_vacant_for_inventory(s.get("availability_status"))
    ]
    if not spaces_list:
        return {"count": 0, "units": []}

    unit_ids = [str(s["unit_id"]) for s in spaces_list if s.get("unit_id")]
    space_by_unit = {str(s["unit_id"]): s for s in spaces_list if s.get("unit_id")}

    units_list: list[dict[str, Any]] = []
    for batch in _chunks(unit_ids):
        ur = (
            client.table("units")
            .select("id,unit,property_id,floorplan_id,created_at,move_in_date")
            .in_("id", batch)
            .execute()
        )
        units_list.extend(ur.data or [])

    prop_ids = list({str(u["property_id"]) for u in units_list if u.get("property_id")})
    prop_names: dict[str, str] = {}
    for batch in _chunks(prop_ids):
        pr = client.table("properties").select("id,name").in_("id", batch).execute()
        for p in pr.data or []:
            prop_names[str(p["id"])] = p.get("name") or "Property"

    if property_name:
        pname_lower = property_name.lower()
        allowed = {pid for pid, n in prop_names.items() if pname_lower in n.lower()}
        units_list = [u for u in units_list if str(u.get("property_id")) in allowed]

    result_units = []
    for u in units_list:
        uid = str(u["id"])
        sp_row = space_by_unit.get(uid) or {}
        avail = sp_row.get("available_date")
        fallback_dt = (
            _parse_ts(sp_row.get("created_at"))
            or _parse_ts(u.get("move_in_date"))
            or _parse_ts(u.get("created_at"))
        )
        vacancy_days = _days_vacant(avail, fallback_dt)
        if days_vacant_min > 0 and vacancy_days < days_vacant_min:
            continue
        pid = str(u.get("property_id") or "")
        result_units.append({
            "unit_number": u.get("unit") or uid[:8],
            "property": prop_names.get(pid, "Unknown"),
            "days_vacant": vacancy_days,
            "available_date": avail,
        })

    result_units.sort(key=lambda x: x["days_vacant"], reverse=True)
    return {"count": len(result_units), "units": result_units}


async def get_vacant_units(
    days_vacant_min: int = 0,
    property_name: str = "",
) -> dict[str, Any]:
    """
    Get units that are currently vacant from the database.
    Use when the user asks about vacant units, empty units, or availability.

    Args:
        days_vacant_min: Only include units vacant for at least this many days.
            Pass 20 if user asks about units vacant for past 20 days. Default 0 means all vacant units.
        property_name: Filter to a specific property by name. Leave empty for all properties.

    Returns:
        Dictionary with count of vacant units and list of unit details.
    """
    return await asyncio.to_thread(_get_vacant_units_sync, days_vacant_min, property_name)


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 2 — At-risk units
# ─────────────────────────────────────────────────────────────────────────────

def _get_at_risk_units_sync(property_name: str = "") -> dict[str, Any]:
    from services.dashboard_service import _build_inventory_vacant_sync
    payload = _build_inventory_vacant_sync(property_id=None, days=7)
    units = payload.get("vacantUnits", [])
    at_risk = [u for u in units if u.get("status") == "atRisk"]
    if property_name:
        at_risk = [u for u in at_risk if property_name.lower() in (u.get("property") or "").lower()]
    return {"count": len(at_risk), "units": at_risk}


async def get_at_risk_units(property_name: str = "") -> dict[str, Any]:
    """
    Get units flagged as at-risk due to low conversion rate below 60 percent.
    Use when user asks about at-risk units, problem units, or units needing urgent action.

    Args:
        property_name: Filter to a specific property by name. Leave empty for all properties.

    Returns:
        Dictionary with count and list of at-risk units.
    """
    return await asyncio.to_thread(_get_at_risk_units_sync, property_name)


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 3 — Property occupancy summary
# ─────────────────────────────────────────────────────────────────────────────

def _get_property_summary_sync(property_name: str = "") -> dict[str, Any]:
    client = get_client()
    props_result = client.table("properties").select("id,name,units").limit(500).execute()
    properties = props_result.data or []
    if property_name:
        properties = [p for p in properties if property_name.lower() in (p.get("name") or "").lower()]
    if not properties:
        return {"count": 0, "properties": []}

    prop_ids = [str(p["id"]) for p in properties]
    units_by_prop: dict[str, int] = {}
    for batch in _chunks(prop_ids):
        ur = (
            client.table("units")
            .select("id,property_id")
            .in_("property_id", batch)
            .eq("active", True)
            .execute()
        )
        for u in ur.data or []:
            pid = str(u["property_id"])
            units_by_prop[pid] = units_by_prop.get(pid, 0) + 1

    unit_ids_all: list[str] = []
    unit_to_prop: dict[str, str] = {}
    for batch in _chunks(prop_ids):
        ur = client.table("units").select("id,property_id").in_("property_id", batch).execute()
        for u in ur.data or []:
            unit_ids_all.append(str(u["id"]))
            unit_to_prop[str(u["id"])] = str(u["property_id"])

    vacant_by_prop: dict[str, int] = {}
    for batch in _chunks(unit_ids_all):
        sp = (
            client.table("spaces")
            .select("unit_id,availability_status")
            .in_("unit_id", batch)
            .execute()
        )
        for s in sp.data or []:
            if _space_is_vacant_for_inventory(s.get("availability_status")):
                uid = str(s["unit_id"])
                pid = unit_to_prop.get(uid, "")
                if pid:
                    vacant_by_prop[pid] = vacant_by_prop.get(pid, 0) + 1

    summary = []
    for prop in properties:
        pid = str(prop["id"])
        total = units_by_prop.get(pid, _safe_int(prop.get("units"), 0))
        vacant = vacant_by_prop.get(pid, 0)
        occupied = max(0, total - vacant)
        occ_pct = round(occupied / total * 100, 1) if total > 0 else 0.0
        summary.append({
            "property": prop.get("name") or "Property",
            "total_units": total,
            "vacant": vacant,
            "occupied": occupied,
            "occupancy_pct": occ_pct,
        })
    return {"count": len(summary), "properties": summary}


async def get_property_summary(property_name: str = "") -> dict[str, Any]:
    """
    Get occupancy statistics per property including total units, vacant, occupied, and occupancy percentage.
    Use when user asks about occupancy rates, portfolio overview, or property stats.

    Args:
        property_name: Filter to a specific property by name. Leave empty for all properties.

    Returns:
        Dictionary with list of properties and their occupancy stats.
    """
    return await asyncio.to_thread(_get_property_summary_sync, property_name)


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 4 — Recent bookings / tours
# ─────────────────────────────────────────────────────────────────────────────

def _get_recent_bookings_sync(
    days: int = 7,
    property_name: str = "",
) -> dict[str, Any]:
    client = get_client()
    days = normalize_dashboard_days(days)
    since = (datetime.now(UTC) - timedelta(days=days)).isoformat()
    bk = (
        client.table("bookings")
        .select("id,start_time,end_time,status,name,phone,floorplan_id")
        .gte("start_time", since)
        .order("start_time", desc=True)
        .limit(100)
        .execute()
    )
    bookings = bk.data or []
    if not bookings:
        return {"count": 0, "bookings": []}

    fp_ids = list({str(b["floorplan_id"]) for b in bookings if b.get("floorplan_id")})
    fp_to_prop: dict[str, str] = {}
    prop_ids: set[str] = set()
    for batch in _chunks(fp_ids):
        fr = client.table("floorplans").select("id,property_id").in_("id", batch).execute()
        for f in fr.data or []:
            fp_to_prop[str(f["id"])] = str(f.get("property_id") or "")
            if f.get("property_id"):
                prop_ids.add(str(f["property_id"]))

    prop_names: dict[str, str] = {}
    for batch in _chunks(list(prop_ids)):
        pr = client.table("properties").select("id,name").in_("id", batch).execute()
        for p in pr.data or []:
            prop_names[str(p["id"])] = p.get("name") or "Property"

    result = []
    for b in bookings:
        fp = str(b.get("floorplan_id") or "")
        pid = fp_to_prop.get(fp, "")
        pname = prop_names.get(pid, "Unknown")
        if property_name and property_name.lower() not in pname.lower():
            continue
        result.append({
            "prospect_name": b.get("name") or "Unknown",
            "property": pname,
            "start_time": b.get("start_time"),
            "status": b.get("status"),
        })
    return {"count": len(result), "bookings": result}


async def get_recent_bookings(
    days: int = 7,
    property_name: str = "",
) -> dict[str, Any]:
    """
    Get recent tour bookings from the database.
    Use when user asks about tours, scheduled visits, booking counts, or follow-ups.

    Args:
        days: Number of past days to look back. Use 7 for this week, 30 for this month, 90 for quarter.
        property_name: Filter to a specific property by name. Leave empty for all properties.

    Returns:
        Dictionary with count and list of bookings.
    """
    return await asyncio.to_thread(_get_recent_bookings_sync, days, property_name)


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 5 — Lead pipeline
# ─────────────────────────────────────────────────────────────────────────────

def _get_lead_pipeline_sync(days: int = 30) -> dict[str, Any]:
    from services.dashboard_service import _build_leads_summary_sync
    days = normalize_dashboard_days(days)
    payload = _build_leads_summary_sync(property_id=None, days=days)
    return {
        "total": payload.get("total", 0),
        "hot": payload.get("hot", 0),
        "warm": payload.get("warm", 0),
        "cold": payload.get("cold", 0),
        "applied": sum(1 for r in payload.get("data", []) if "Applied" in r.get("tags", [])),
        "leased": sum(1 for r in payload.get("data", []) if "Leased" in r.get("tags", [])),
    }


async def get_lead_pipeline(days: int = 30) -> dict[str, Any]:
    """
    Get lead and prospect pipeline statistics including total, hot, warm, cold, applied, leased counts.
    Use when user asks about leads, pipeline, prospects, or conversion.

    Args:
        days: Rolling window in days. Use 7, 30, or 90.

    Returns:
        Dictionary with total, hot, warm, cold, applied, leased counts.
    """
    return await asyncio.to_thread(_get_lead_pipeline_sync, days)


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 6 — Stale units
# ─────────────────────────────────────────────────────────────────────────────

def _get_stale_units_sync(property_name: str = "") -> dict[str, Any]:
    from services.dashboard_service import _build_inventory_vacant_sync
    payload = _build_inventory_vacant_sync(property_id=None, days=7)
    units = payload.get("vacantUnits", [])
    stale = [u for u in units if u.get("status") == "stale"]
    if property_name:
        stale = [u for u in stale if property_name.lower() in (u.get("property") or "").lower()]
    return {"count": len(stale), "units": stale}


async def get_stale_units(property_name: str = "") -> dict[str, Any]:
    """
    Get units with moderate conversion rate between 60 and 90 percent flagged as stale.
    Use when user asks about stale listings or underperforming units.

    Args:
        property_name: Filter to a specific property by name. Leave empty for all properties.

    Returns:
        Dictionary with count and list of stale units.
    """
    return await asyncio.to_thread(_get_stale_units_sync, property_name)


# ─────────────────────────────────────────────────────────────────────────────
# Export all tool functions for ADK registration
# ─────────────────────────────────────────────────────────────────────────────

ALL_TOOL_FUNCTIONS = [
    get_vacant_units,
    get_at_risk_units,
    get_property_summary,
    get_recent_bookings,
    get_lead_pipeline,
    get_stale_units,
]
