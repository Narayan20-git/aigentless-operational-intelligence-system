"""
Live dashboard payloads from Supabase tables (no ui_payloads).

Lead Prioritization (/api/leads/summary):
  prospects -> prospect_events (prospect_id), properties (property_id),
  units (property_id), bookings (profile_id = prospect id for seeded rows).

Inventory (/api/inventory/vacant-units):
  spaces (unit_id -> units.id) -> properties, floorplans,
  tour_steps (unit_id), bookings (floorplan_id, applications proxy).
"""
import asyncio
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta
from typing import Any

from config.database import get_client

_IN_CHUNK = 12


def normalize_dashboard_days(days: int) -> int:
    if days in (7, 30, 90):
        return days
    return 7


def _chunks(seq: list[Any], size: int = _IN_CHUNK):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def _parse_ts(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        try:
            s = value.replace("Z", "+00:00")
            return datetime.fromisoformat(s)
        except ValueError:
            return None
    return None


def _heat_from_engagement(
    events: list[dict[str, Any]],
    last_ts: datetime | None,
    created_ts: datetime | None,
    has_booking: bool,
) -> str:
    """Derive hot/warm/cold from events already scoped to the selected date range + recency + bookings."""
    now = datetime.now(UTC)
    n_in = len(events)

    ref = last_ts or created_ts
    hours: float | None = None
    if ref:
        r = ref if ref.tzinfo else ref.replace(tzinfo=UTC)
        hours = (now - r).total_seconds() / 3600.0

    if has_booking or n_in >= 3 or (hours is not None and hours < 24):
        return "hot"
    if n_in >= 1 or (hours is not None and hours < 24 * 7):
        return "warm"
    return "cold"


def _priority_from_flags(applied: bool | None, leased: bool | None) -> str:
    a, l = bool(applied), bool(leased)
    if not a and not l:
        return "critical"
    if a and not l:
        return "moderate"
    return "low"


def _build_leads_summary_sync(property_id: str | None = None, days: int = 7) -> dict[str, Any]:
    """Live data from prospects, prospect_events, properties, units."""
    client = get_client()
    days = normalize_dashboard_days(days)
    since = datetime.now(UTC) - timedelta(days=days)
    pres = (
        client.table("prospects")
        .select("id,first_name,last_name,applied,leased,created_at,ignore")
        .order("created_at", desc=True)
        .limit(80)
        .execute()
    )
    rows_in = [r for r in (pres.data or []) if not r.get("ignore")]
    if not rows_in:
        return {"total": 0, "hot": 0, "warm": 0, "cold": 0, "data": []}

    p_ids = [str(r["id"]) for r in rows_in]
    events_raw: list[dict[str, Any]] = []
    chunk = 40
    for i in range(0, len(p_ids), chunk):
        part = p_ids[i : i + chunk]
        er = (
            client.table("prospect_events")
            .select("prospect_id,property_id,timestamp,event")
            .in_("prospect_id", part)
            .execute()
        )
        events_raw.extend(er.data or [])

    by_prospect: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for e in events_raw:
        pid = str(e.get("prospect_id") or "")
        if pid:
            by_prospect[pid].append(e)

    booking_by_prospect: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for i in range(0, len(p_ids), chunk):
        part = p_ids[i : i + chunk]
        br = (
            client.table("bookings")
            .select("profile_id,start_time,end_time")
            .in_("profile_id", part)
            .execute()
        )
        for row in br.data or []:
            pid = str(row.get("profile_id") or "")
            if pid:
                booking_by_prospect[pid].append(row)

    fp_for_prop: set[str] = set()
    if property_id:
        fr = client.table("floorplans").select("id").eq("property_id", property_id).limit(500).execute()
        fp_for_prop = {str(x["id"]) for x in (fr.data or [])}

    if property_id:
        def _prospect_in_property(prow: dict[str, Any]) -> bool:
            pr = str(prow["id"])
            evs = by_prospect.get(pr, [])
            if any(str(e.get("property_id")) == property_id for e in evs):
                return True
            for b in booking_by_prospect.get(pr, []):
                if str(b.get("floorplan_id")) in fp_for_prop:
                    return True
            return False

        rows_in = [r for r in rows_in if _prospect_in_property(r)]
        if not rows_in:
            return {"total": 0, "hot": 0, "warm": 0, "cold": 0, "data": []}

    prop_ids_set: set[str] = set()
    for e in events_raw:
        pid = e.get("property_id")
        if pid:
            prop_ids_set.add(str(pid))
    if property_id:
        prop_ids_set.add(property_id)

    prop_names: dict[str, str] = {}
    for batch in _chunks(list(prop_ids_set), _IN_CHUNK):
        pr = client.table("properties").select("id,name").in_("id", batch).execute()
        for p in pr.data or []:
            prop_names[str(p["id"])] = p.get("name") or "Property"

    # One unit per property for display (first by unit code)
    units_by_prop: dict[str, dict[str, Any]] = {}
    if property_id:
        ur = (
            client.table("units")
            .select("id,unit,property_id")
            .eq("property_id", property_id)
            .order("unit")
            .limit(200)
            .execute()
        )
        for u in ur.data or []:
            pidu = str(u.get("property_id") or "")
            if pidu and pidu not in units_by_prop:
                units_by_prop[pidu] = u
    elif prop_ids_set:
        for batch in _chunks(list(prop_ids_set), _IN_CHUNK):
            ur = (
                client.table("units")
                .select("id,unit,property_id")
                .in_("property_id", batch)
                .order("unit")
                .limit(200)
                .execute()
            )
            for u in ur.data or []:
                pidu = str(u.get("property_id") or "")
                if pidu and pidu not in units_by_prop:
                    units_by_prop[pidu] = u

    lead_rows: list[dict[str, Any]] = []
    hot = warm = cold = 0

    for r in rows_in:
        pid = str(r["id"])
        created = _parse_ts(r.get("created_at"))
        evs = by_prospect.get(pid, [])

        def _in_selected_range(ts_raw: Any) -> bool:
            t = _parse_ts(ts_raw)
            if not t:
                return False
            if t.tzinfo is None:
                t = t.replace(tzinfo=UTC)
            return t >= since

        evs_w = [e for e in evs if _in_selected_range(e.get("timestamp"))]
        bks_w = [b for b in booking_by_prospect.get(pid, []) if _in_selected_range(b.get("start_time"))]
        evs_display = evs_w if evs_w else evs
        evs_sorted = sorted(
            evs_display,
            key=lambda x: _parse_ts(x.get("timestamp")) or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )
        last_ev = evs_sorted[0] if evs_sorted else None
        last_ts = _parse_ts(last_ev.get("timestamp")) if last_ev else None

        all_ts: list[datetime] = []
        for e in evs_display:
            t = _parse_ts(e.get("timestamp"))
            if t:
                all_ts.append(t if t.tzinfo else t.replace(tzinfo=UTC))
        last_contact_dt = max(all_ts) if all_ts else None

        tour_candidates: list[datetime] = []
        for e in evs_w:
            evname = (e.get("event") or "").lower()
            if "tour" in evname:
                t = _parse_ts(e.get("timestamp"))
                if t:
                    tour_candidates.append(t if t.tzinfo else t.replace(tzinfo=UTC))
        tour_ts = max(tour_candidates) if tour_candidates else None
        if tour_ts is None:
            booking_starts: list[datetime] = []
            for b in bks_w:
                t = _parse_ts(b.get("start_time"))
                if t:
                    booking_starts.append(t if t.tzinfo else t.replace(tzinfo=UTC))
            if not booking_starts:
                for b in booking_by_prospect.get(pid, []):
                    t = _parse_ts(b.get("start_time"))
                    if t:
                        booking_starts.append(t if t.tzinfo else t.replace(tzinfo=UTC))
            tour_ts = max(booking_starts) if booking_starts else None

        last_ts_heat: datetime | None = None
        if evs_w:
            ev_sw = sorted(
                evs_w,
                key=lambda x: _parse_ts(x.get("timestamp")) or datetime.min.replace(tzinfo=UTC),
                reverse=True,
            )
            last_ts_heat = _parse_ts(ev_sw[0].get("timestamp")) if ev_sw else None
        has_booking = len(bks_w) > 0
        heat = _heat_from_engagement(evs_w, last_ts_heat, created, has_booking)
        if heat == "hot":
            hot += 1
        elif heat == "warm":
            warm += 1
        else:
            cold += 1

        prid = str(last_ev.get("property_id")) if last_ev and last_ev.get("property_id") else None
        if not prid and evs_sorted:
            for e in reversed(evs_sorted):
                if e.get("property_id"):
                    prid = str(e["property_id"])
                    break

        prop_name = prop_names.get(prid, "Property") if prid else "Property"
        unit_row = units_by_prop.get(prid) if prid else None
        unit_label = (unit_row.get("unit") or "—") if unit_row else "—"

        fn = (r.get("first_name") or "").strip()
        ln = (r.get("last_name") or "").strip()
        name = f"{fn} {ln}".strip() or "Lead"

        tour_dt = tour_ts or last_contact_dt or created or datetime.now(UTC)
        contact_dt = last_contact_dt or last_ts or created or datetime.now(UTC)
        tour_iso = tour_dt.isoformat()
        contact_iso = contact_dt.isoformat()

        priority = _priority_from_flags(r.get("applied"), r.get("leased"))

        tags: list[str] = []
        if r.get("leased"):
            tags.append("Leased")
        elif r.get("applied"):
            tags.append("Applied")
        else:
            tags.append("New Lead")

        lead_rows.append(
            {
                "id": pid,
                "name": name,
                "status": heat,
                "priority": priority,
                "property": prop_name,
                "unit": unit_label,
                "tour_time": tour_iso,
                "last_contact": contact_iso,
                "tags": tags,
                "recommended_action": "Share limited-time offer and schedule a call",
                "objections": ["Budget", "Move-in timing"],
                "alternates": ["Unit with lower rent", "Flexible move-in date"],
                "ai_draft": "Hi! We have a matching option available this week.",
            }
        )

    return {
        "total": len(lead_rows),
        "hot": hot,
        "warm": warm,
        "cold": cold,
        "data": lead_rows,
    }


def _days_vacant(available_date: Any, fallback: datetime | None) -> int:
    today = date.today()
    if available_date:
        try:
            if isinstance(available_date, date) and not isinstance(available_date, datetime):
                d = available_date
            else:
                d = date.fromisoformat(str(available_date)[:10])
            return max(0, (today - d).days)
        except (ValueError, TypeError):
            pass
    if fallback:
        if fallback.tzinfo is None:
            fallback = fallback.replace(tzinfo=UTC)
        return max(0, (date.today() - fallback.date()).days)
    return 0


def _conversion_rate_pct(tours: int, apps: int) -> float:
    """Conversion = applications / tours, capped to 100% and safe for tours=0."""
    if tours <= 0:
        return 0.0
    return min(100.0, (apps / tours) * 100.0)


def _inventory_status_from_conversion(conv_pct: float) -> str:
    """healthy: >90%; stale (moderate): 60–90%; atRisk (critical): <60%."""
    if conv_pct > 90:
        return "healthy"
    if conv_pct >= 60:
        return "stale"
    return "atRisk"


def _space_is_vacant_for_inventory(status_val: Any) -> bool:
    """Match common PMS / migration values; seed used lowercase 'available' only."""
    raw = str(status_val or "").strip().lower().replace(" ", "_")
    if not raw:
        return False
    if raw in (
        "available",
        "vacant",
        "unoccupied",
        "open",
        "listed",
        "vacant_ready",
        "vacant-ready",
        "move_in_ready",
        "move-in-ready",
    ):
        return True
    # e.g. "notice" (on notice) is not yet vacant — exclude unless clearly available
    if "unavail" in raw or raw in ("leased", "occupied", "notice"):
        return False
    return False


def _tour_steps_counts_by_unit(client: Any, unit_ids: list[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    if not unit_ids:
        return counts
    for batch in _chunks(list(unit_ids), _IN_CHUNK):
        ts = client.table("tour_steps").select("unit_id").in_("unit_id", batch).execute()
        for row in ts.data or []:
            u = row.get("unit_id")
            if u:
                counts[str(u)] += 1
    return counts


def _booking_counts_since_by_floorplan(client: Any, fp_ids: list[str], since: datetime) -> Counter[str]:
    counts: Counter[str] = Counter()
    if not fp_ids:
        return counts
    since_iso = since.isoformat()
    for batch in _chunks(list(fp_ids), _IN_CHUNK):
        try:
            bk = (
                client.table("bookings")
                .select("floorplan_id,start_time")
                .in_("floorplan_id", batch)
                .gte("start_time", since_iso)
                .execute()
            )
            rows = bk.data or []
        except Exception:
            bk = client.table("bookings").select("floorplan_id,start_time").in_("floorplan_id", batch).execute()
            rows = []
            for row in bk.data or []:
                t = _parse_ts(row.get("start_time"))
                if not t:
                    continue
                if t.tzinfo is None:
                    t = t.replace(tzinfo=UTC)
                if t >= since:
                    rows.append(row)
        for row in rows:
            fp = row.get("floorplan_id")
            if fp:
                counts[str(fp)] += 1
    return counts


def _floorplan_bedrooms_map(client: Any, fp_ids: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    if not fp_ids:
        return out
    for batch in _chunks(list(fp_ids), _IN_CHUNK):
        fpr = client.table("floorplans").select("id,bedrooms").in_("id", batch).execute()
        for fp in fpr.data or []:
            out[str(fp["id"])] = str(fp.get("bedrooms") or "1")
    return out


def _build_inventory_vacant_sync(property_id: str | None = None, days: int = 7) -> dict[str, Any]:
    """Live vacant inventory from spaces + units + properties; metrics from tour_steps + bookings."""
    client = get_client()
    days = normalize_dashboard_days(days)
    since = datetime.now(UTC) - timedelta(days=days)
    sp = (
        client.table("spaces")
        .select("unit_id,available_date,availability_status,created_at")
        .limit(400)
        .execute()
    )
    spaces_list = [s for s in (sp.data or []) if _space_is_vacant_for_inventory(s.get("availability_status"))]
    spaces_list = spaces_list[:120]
    if not spaces_list:
        return {
            "page": {"title": "Inventory Intelligence", "description": "Vacancy and conversion health"},
            "metricCards": [
                {"id": "vacant", "value": "0", "label": "Vacant Units"},
                {"id": "atRisk", "value": "0", "label": "At Risk"},
                {"id": "stale", "value": "0", "label": "Stale"},
            ],
            "tableTitle": "Vacant Units",
            "emptyStateText": "No vacant inventory",
            "statusFilterLabels": {
                "all": "All",
                "atRisk": "At Risk",
                "stale": "Stale",
                "healthy": "Healthy",
            },
            "vacantUnits": [],
        }

    unit_ids: list[str] = []
    space_by_unit: dict[str, dict[str, Any]] = {}
    for s in spaces_list:
        uid = s.get("unit_id")
        if not uid:
            continue
        uid = str(uid)
        if uid not in space_by_unit:
            unit_ids.append(uid)
        space_by_unit[uid] = s

    if not unit_ids:
        vacant_units: list[dict[str, Any]] = []
    else:
        units_list: list[dict[str, Any]] = []
        for batch in _chunks(unit_ids, _IN_CHUNK):
            ur = (
                client.table("units")
                .select("id,unit,property_id,floorplan_id,created_at,move_in_date")
                .in_("id", batch)
                .execute()
            )
            units_list.extend(ur.data or [])
        if property_id:
            units_list = [u for u in units_list if str(u.get("property_id")) == property_id]

        prop_ids = list({str(u["property_id"]) for u in units_list if u.get("property_id")})
        prop_names: dict[str, str] = {}
        for batch in _chunks(prop_ids, _IN_CHUNK):
            pr = client.table("properties").select("id,name").in_("id", batch).execute()
            for p in pr.data or []:
                prop_names[str(p["id"])] = p.get("name") or "Property"

        uuid_list = [str(u["id"]) for u in units_list]
        tour_counts = _tour_steps_counts_by_unit(client, uuid_list)

        fp_ids = list({str(u["floorplan_id"]) for u in units_list if u.get("floorplan_id")})
        app_counts = _booking_counts_since_by_floorplan(client, fp_ids, since)

        fp_bedrooms = _floorplan_bedrooms_map(client, fp_ids)

        vacant_units = []
        for u in units_list:
            uid = str(u["id"])
            sp_row = space_by_unit.get(uid) or {}
            pid = str(u.get("property_id") or "")
            pname = prop_names.get(pid, "Property")
            fp = str(u.get("floorplan_id") or "")
            avail = sp_row.get("available_date")
            fallback_dt = _parse_ts(sp_row.get("created_at")) or _parse_ts(u.get("move_in_date")) or _parse_ts(u.get("created_at"))
            vacancy_days = _days_vacant(avail, fallback_dt)
            tours_n = tour_counts.get(uid, 0)
            raw_apps = app_counts.get(fp, 0) if fp else 0
            # Bookings are floorplan-level in this schema; keep unit rows internally consistent.
            apps_n = min(raw_apps, tours_n)
            conv_float = _conversion_rate_pct(tours_n, apps_n)
            conv_pct_int = int(round(conv_float))
            status = _inventory_status_from_conversion(conv_float)
            br = fp_bedrooms.get(fp, "1") if fp else "1"
            utype = f"{br} BR"

            vacant_units.append(
                {
                    "id": uid,
                    "propertyId": pid,
                    "unitCode": u.get("unit") or uid[:8],
                    "property": pname,
                    "unitType": utype,
                    "status": status,
                    "days": vacancy_days,
                    "tours": tours_n,
                    "apps": apps_n,
                    "conv": f"{conv_pct_int}%",
                    "whyMatters": "Availability velocity is below benchmark.",
                    "recommendedAction": "Run pricing + content refresh experiment for 7 days",
                }
            )

        vacant_units = vacant_units[:30]

    n = len(vacant_units)
    at_risk = sum(1 for x in vacant_units if x["status"] == "atRisk")
    stale_n = sum(1 for x in vacant_units if x["status"] == "stale")

    return {
        "page": {"title": "Inventory Intelligence", "description": "Vacancy and conversion health"},
        "metricCards": [
            {"id": "vacant", "value": str(n), "label": "Vacant Units"},
            {"id": "atRisk", "value": str(at_risk), "label": "At Risk"},
            {"id": "stale", "value": str(stale_n), "label": "Stale"},
        ],
        "tableTitle": "Vacant Units",
        "emptyStateText": "No vacant inventory",
        "statusFilterLabels": {
            "all": "All",
            "atRisk": "At Risk",
            "stale": "Stale",
            "healthy": "Healthy",
        },
        "vacantUnits": vacant_units,
    }


def _list_property_options_sync() -> list[dict[str, str]]:
    client = get_client()
    r = client.table("properties").select("id,name").order("name").limit(500).execute()
    return [{"id": str(x["id"]), "name": (x.get("name") or "Property").strip()} for x in (r.data or [])]


async def get_property_options_payload() -> list[dict[str, str]]:
    return await asyncio.to_thread(_list_property_options_sync)


async def get_home_payload(property_id: str | None = None, days: int = 7) -> dict[str, Any]:
    from services.live_ui_payloads import build_home_payload

    d = normalize_dashboard_days(days)
    return await asyncio.to_thread(build_home_payload, property_id, d)


async def get_leads_summary_payload(property_id: str | None = None, days: int = 7) -> dict[str, Any]:
    d = normalize_dashboard_days(days)
    return await asyncio.to_thread(_build_leads_summary_sync, property_id, d)


async def get_inventory_payload(property_id: str | None = None, days: int = 7) -> dict[str, Any]:
    d = normalize_dashboard_days(days)
    return await asyncio.to_thread(_build_inventory_vacant_sync, property_id, d)


async def get_property_onboarding_payload(property_id: str | None = None, days: int = 7) -> dict[str, Any]:
    from services.live_ui_payloads import build_onboarding_payload

    d = normalize_dashboard_days(days)
    return await asyncio.to_thread(build_onboarding_payload, property_id, d)


async def get_portfolio_overview_payload(property_id: str | None = None, days: int = 7) -> dict[str, Any]:
    from services.live_ui_payloads import build_portfolio_overview

    d = normalize_dashboard_days(days)
    return await asyncio.to_thread(build_portfolio_overview, property_id, d)


async def get_weekly_brief_payload() -> dict[str, Any]:
    from services.live_ui_payloads import build_weekly_brief

    return await asyncio.to_thread(build_weekly_brief)


async def get_integrations_payload() -> dict[str, Any]:
    from services.live_ui_payloads import build_integrations_payload

    return await asyncio.to_thread(build_integrations_payload)


async def get_profile_payload() -> dict[str, Any]:
    from services.live_ui_payloads import build_profile_payload

    return await asyncio.to_thread(build_profile_payload)


async def get_header_payload() -> dict[str, Any]:
    from services.live_ui_payloads import build_header_payload

    return await asyncio.to_thread(build_header_payload)


async def get_navigation_payload() -> dict[str, Any]:
    from services.live_ui_payloads import build_navigation_payload

    return await asyncio.to_thread(build_navigation_payload)
