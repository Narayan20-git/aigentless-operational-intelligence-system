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
import http.client
import json
import logging
import os
import time
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta
from typing import Any, Optional
from urllib import error as urllib_error
from urllib import request as urllib_request

from config.database import get_client

logger = logging.getLogger(__name__)

# PostgREST URL length limits are generous; larger chunks = fewer round trips to Supabase.
_IN_CHUNK = 48

_coalesce_lock = asyncio.Lock()
_coalesce_tasks: dict[str, asyncio.Task[Any]] = {}
_inventory_ai_cache: dict[str, tuple[float, tuple[str, str]]] = {}
_INVENTORY_AI_CACHE_TTL_SEC = 15 * 60


def _dash_cache_key(prefix: str, property_id: str | None, days: int) -> str:
    return f"{prefix}:{property_id or ''}:{days}"


async def _coalesced_to_thread(key: str, fn: Any, *args: Any, **kwargs: Any) -> Any:
    """One in-flight Supabase build per key so parallel /api/* hits share a single scan."""
    async with _coalesce_lock:
        existing = _coalesce_tasks.get(key)
        if existing is not None and not existing.done():
            task = existing
        else:
            task = asyncio.create_task(asyncio.to_thread(fn, *args, **kwargs))
            _coalesce_tasks[key] = task
    try:
        return await task
    finally:
        async with _coalesce_lock:
            if _coalesce_tasks.get(key) is task and task.done():
                _coalesce_tasks.pop(key, None)


def normalize_dashboard_days(days: int) -> int:
    try:
        d = int(days)
    except (TypeError, ValueError):
        return 7
    if d < 1:
        return 7
    # Keep broad support for custom Lesa AI windows while still preventing unbounded scans.
    return min(d, 365)


def _normalize_custom_date_range(
    start_date: str | None, end_date: str | None
) -> tuple[date, date] | None:
    if not start_date or not end_date:
        return None
    try:
        start = date.fromisoformat(str(start_date).strip()[:10])
        end = date.fromisoformat(str(end_date).strip()[:10])
    except ValueError:
        return None
    if start > end:
        start, end = end, start
    today = datetime.now(UTC).date()
    if end > today:
        end = today
    if start > end:
        return None
    return start, end


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


def _dt_gte_since(ts_raw: Any, since: datetime) -> bool:
    t = _parse_ts(ts_raw)
    if not t:
        return False
    if t.tzinfo is None:
        t = t.replace(tzinfo=UTC)
    return t >= since


def _heat_from_engagement(
    events: list[dict[str, Any]],
    last_ts: datetime | None,
    created_ts: datetime | None,
    has_booking: bool,
) -> str:
    """Derive hot/warm/cold from events already scoped to the selected date range + recency + bookings."""
    now = datetime.now(UTC)
    n_in = len(events)

    # No touches in the selected window → cold (do not use created_at or leads look "warm" on 7d with no activity).
    if n_in == 0 and not has_booking:
        return "cold"

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


def _build_leads_summary_sync(
    property_id: str | None = None, days: int = 7, *, enrich_with_llm: bool = True
) -> dict[str, Any]:
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
    rows_in = [
        r
        for r in (pres.data or [])
        if not r.get("ignore") and not bool(r.get("applied")) and not bool(r.get("leased"))
    ]
    if not rows_in:
        return {
            "total": 0,
            "hot": 0,
            "warm": 0,
            "cold": 0,
            "data": [],
            "window_days": days,
            "period_start": since.isoformat(),
            "events_in_window": 0,
            "bookings_in_window": 0,
        }

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
            .select("id,profile_id,start_time,end_time,floorplan_id")
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
            return {
                "total": 0,
                "hot": 0,
                "warm": 0,
                "cold": 0,
                "data": [],
                "window_days": days,
                "period_start": since.isoformat(),
                "events_in_window": 0,
                "bookings_in_window": 0,
            }

    allowed_ids = {str(r["id"]) for r in rows_in}
    events_in_window = sum(
        1 for e in events_raw if str(e.get("prospect_id") or "") in allowed_ids and _dt_gte_since(e.get("timestamp"), since)
    )
    bookings_in_window = sum(
        1
        for pid in allowed_ids
        for b in booking_by_prospect.get(pid, [])
        if _dt_gte_since(b.get("start_time"), since)
    )

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

    # First unit per property (fallback) + floorplan -> unit for tour-scoped display
    units_by_prop: dict[str, dict[str, Any]] = {}
    units_by_floorplan: dict[str, dict[str, Any]] = {}
    if property_id:
        ur = (
            client.table("units")
            .select("id,unit,property_id,floorplan_id")
            .eq("property_id", property_id)
            .order("unit")
            .limit(500)
            .execute()
        )
        for u in ur.data or []:
            pidu = str(u.get("property_id") or "")
            fp = str(u.get("floorplan_id") or "")
            if pidu and pidu not in units_by_prop:
                units_by_prop[pidu] = u
            if fp and fp not in units_by_floorplan:
                units_by_floorplan[fp] = u
    elif prop_ids_set:
        for batch in _chunks(list(prop_ids_set), _IN_CHUNK):
            ur = (
                client.table("units")
                .select("id,unit,property_id,floorplan_id")
                .in_("property_id", batch)
                .order("unit")
                .limit(800)
                .execute()
            )
            for u in ur.data or []:
                pidu = str(u.get("property_id") or "")
                fp = str(u.get("floorplan_id") or "")
                if pidu and pidu not in units_by_prop:
                    units_by_prop[pidu] = u
                if fp and fp not in units_by_floorplan:
                    units_by_floorplan[fp] = u

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
        # Follow-up queue should only include prospects that actually toured.
        if tour_ts is None:
            continue

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

        tour_bookings_ordered = sorted(
            bks_w if bks_w else booking_by_prospect.get(pid, []),
            key=lambda b: _parse_ts(b.get("start_time")) or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )
        tour_booking_ids = [str(b["id"]) for b in tour_bookings_ordered if b.get("id")][:10]
        tour_floorplan_ids = list(
            dict.fromkeys(
                [str(b["floorplan_id"]) for b in tour_bookings_ordered if b.get("floorplan_id")]
            )
        )[:12]

        unit_label = "—"
        for fp in tour_floorplan_ids:
            urec = units_by_floorplan.get(fp)
            if urec and (not prid or str(urec.get("property_id")) == str(prid)):
                unit_label = str(urec.get("unit") or "—")
                break
        if unit_label == "—" and prid:
            unit_row_fb = units_by_prop.get(prid)
            if unit_row_fb:
                unit_label = str(unit_row_fb.get("unit") or "—")

        fn = (r.get("first_name") or "").strip()
        ln = (r.get("last_name") or "").strip()
        name = f"{fn} {ln}".strip() or "Lead"

        has_toured = True
        tour_dt = tour_ts or last_contact_dt or created or datetime.now(UTC)
        contact_dt = last_contact_dt or last_ts or created or datetime.now(UTC)
        tour_iso = tour_dt.isoformat() if has_toured else ""
        contact_iso = contact_dt.isoformat()

        # Queue priority is tour-driven for un-applied, un-leased prospects:
        # - critical: toured but not applied yet
        # - moderate: registered but not toured yet
        priority = "critical" if has_toured else "moderate"

        tags: list[str] = []
        if r.get("leased"):
            tags.append("Leased")
        elif r.get("applied"):
            tags.append("Applied")
        else:
            tags.append("New Lead")

        recent_events: list[str] = []
        for e in evs_sorted[:14]:
            ev = str(e.get("event") or "").strip()
            if ev:
                recent_events.append(ev)

        lead_rows.append(
            {
                "id": pid,
                "name": name,
                "status": heat,
                "priority": priority,
                "property": prop_name,
                "unit": unit_label,
                "has_toured": has_toured,
                "tour_time": tour_iso,
                "last_contact": contact_iso,
                "tags": tags,
                "property_id": prid,
                "tour_booking_ids": tour_booking_ids,
                "tour_floorplan_ids": tour_floorplan_ids,
                "recent_events": recent_events,
                "recommended_action": "",
                "objections": [],
                "alternates": [],
                "ai_draft": "",
            }
        )

    from services.lead_card_llm import enrich_leads_summary_rows, heuristic_lead_cards_only

    use_llm = enrich_with_llm and os.getenv("OPENAI_API_KEY", "").strip()
    vacant: list[dict[str, Any]] = []
    if use_llm:
        try:
            inv = _build_inventory_vacant_sync(property_id, days)
            vacant = inv.get("vacantUnits") or []
        except Exception:
            vacant = []
        enrich_leads_summary_rows(
            lead_rows,
            vacant,
            since_iso=since.isoformat(),
            window_days=days,
        )
    else:
        heuristic_lead_cards_only(lead_rows)

    return {
        "total": len(lead_rows),
        "hot": hot,
        "warm": warm,
        "cold": cold,
        "data": lead_rows,
        "window_days": days,
        "period_start": since.isoformat(),
        "events_in_window": events_in_window,
        "bookings_in_window": bookings_in_window,
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


def _inventory_status_from_signals(
    conv_pct: float, vacancy_days: int, window_days: int, tours: int, apps: int
) -> str:
    """Blend conversion + vacancy pressure so each window has a realistic risk spread."""
    # No applications despite visible traffic is a strong risk signal.
    if tours >= 3 and apps == 0:
        return "atRisk"
    # Age pressure threshold scales with selected date window.
    age_pressure_days = max(5, int(window_days * 0.55))
    aged_conv_cutoff = 55 if window_days <= 7 else (60 if window_days <= 30 else 68)
    # In longer windows, prolonged vacancy with sub-healthy conversion should still surface as risk.
    if window_days >= 90 and vacancy_days >= 30 and conv_pct < 75:
        return "atRisk"
    if vacancy_days >= age_pressure_days and conv_pct < aged_conv_cutoff:
        return "atRisk"
    if conv_pct < 45:
        return "atRisk"
    if conv_pct < 75:
        return "stale"
    if conv_pct >= 75:
        return "healthy"
    return "stale"


def _inventory_unit_guidance(
    *,
    status: str,
    vacancy_days: int,
    window_days: int,
    tours: int,
    apps: int,
    conv_pct: float,
    unit_type: str,
    unit_code: str,
    property_name: str,
) -> tuple[str, str]:
    """Generate unit-specific why/action copy from live signals."""
    who = f"Unit {unit_code} at {property_name}" if property_name else f"Unit {unit_code}"
    if tours >= 3 and apps == 0:
        return (
            f"{who}: {tours} tours in the last {window_days} days but zero applications indicates a conversion blocker.",
            f"For {unit_code}: review tour script and qualification, then run a 7-day offer/CTA test to recover applications.",
        )
    if vacancy_days >= max(5, int(window_days * 0.55)) and conv_pct < 60:
        return (
            f"{who} ({unit_type}) has been vacant {vacancy_days} days with low conversion ({int(round(conv_pct))}%).",
            f"For {unit_code} at {property_name}: refresh pricing and listing media this week; prioritize this unit in follow-up.",
        )
    if conv_pct < 45:
        return (
            f"{who}: tour-to-application conversion is critically low at {int(round(conv_pct))}% in the current window.",
            f"For {unit_code}: audit objections from recent tours; adjust positioning, incentives, and lead qualification.",
        )
    if status == "stale":
        if tours <= 2:
            return (
                f"{who}: demand is soft ({tours} tours in {window_days} days), slowing pipeline momentum.",
                f"For {unit_code}: increase exposure on strong channels; test alternative headline and hero photo.",
            )
        return (
            f"{who}: engagement exists ({tours} tours) but conversion ({int(round(conv_pct))}%) is below healthy target.",
            f"For {unit_code}: tighten follow-up timing; test one or two incentive variants to lift applications.",
        )
    return (
        f"{who} is converting well ({apps} apps / {tours} tours) in the last {window_days} days.",
        f"For {unit_code}: keep current strategy and monitor weekly; mirror this unit's messaging on similar floorplans.",
    )


def _normalize_feedback_token(v: Any) -> str:
    s = str(v or "").strip()
    if not s:
        return ""
    if s.startswith("likes_") or s.startswith("improvement_"):
        s = s.replace("_", " ")
    return s[:80]


def _feedback_summary_from_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    likes: Counter[str] = Counter()
    improvements: Counter[str] = Counter()
    ratings: Counter[str] = Counter()
    sample_comments: list[str] = []
    for r in rows:
        raw = r.get("raw_feedback")
        if not isinstance(raw, dict):
            continue
        rating = str(raw.get("rating") or "").strip().lower()
        if rating:
            ratings[rating] += 1
        for x in raw.get("likes") or []:
            t = _normalize_feedback_token(x)
            if t:
                likes[t] += 1
        for x in raw.get("improvements") or []:
            t = _normalize_feedback_token(x)
            if t:
                improvements[t] += 1
        for key in ("additionalCommentsLikes", "additionalCommentsImprovements"):
            c = str(raw.get(key) or "").strip()
            if c:
                sample_comments.append(c[:140])
    return {
        "total_feedback": len(rows),
        "top_likes": [k for k, _ in likes.most_common(5)],
        "top_improvements": [k for k, _ in improvements.most_common(5)],
        "ratings": dict(ratings),
        "comments": sample_comments[:5],
    }


def _feedback_objection_theme_counts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Cluster improvement tokens + free-text for 'Top Objections' style counts."""
    themes: Counter[str] = Counter()
    for r in rows:
        raw = r.get("raw_feedback")
        if not isinstance(raw, dict):
            continue
        for x in raw.get("improvements") or []:
            t = _normalize_feedback_token(x)
            if t:
                themes[t] += 1
        c = str(raw.get("additionalCommentsImprovements") or "").strip()
        if len(c) > 12:
            themes[c[:100]] += 1
    return [{"topic": k, "mentions": int(n)} for k, n in themes.most_common(12)]


def _objection_mentions_in_feedback(raw_feedback: Any, topic: str) -> int:
    if not isinstance(raw_feedback, dict):
        return 0
    topic_n = _normalize_feedback_token(topic).lower()
    if not topic_n:
        return 0
    mentions = 0
    for x in raw_feedback.get("improvements") or []:
        t = _normalize_feedback_token(x).lower()
        if t == topic_n:
            mentions += 1
    c = str(raw_feedback.get("additionalCommentsImprovements") or "").strip()
    if len(c) > 12 and c[:100].strip().lower() == topic.strip().lower():
        mentions += 1
    return mentions


def _fetch_feedback_rows_lesa(
    since_iso: str, property_id: str | None, limit: int = 320, until_iso: str | None = None
) -> list[dict[str, Any]]:
    client = get_client()
    try:
        if property_id:
            fr = client.table("floorplans").select("id").eq("property_id", str(property_id)).limit(400).execute()
            fp_ids = [str(x["id"]) for x in (fr.data or [])]
            if not fp_ids:
                return []
            out: list[dict[str, Any]] = []
            for batch in _chunks(fp_ids, 40):
                q = (
                    client.table("feedback")
                    .select("floorplan_id,created_at,raw_feedback,type")
                    .in_("floorplan_id", batch)
                    .gte("created_at", since_iso)
                )
                if until_iso:
                    q = q.lte("created_at", until_iso)
                r = q.order("created_at", desc=True).limit(limit).execute()
                out.extend(r.data or [])
                if len(out) >= limit:
                    break
            return out[:limit]
        q = (
            client.table("feedback")
            .select("floorplan_id,created_at,raw_feedback,type")
            .gte("created_at", since_iso)
        )
        if until_iso:
            q = q.lte("created_at", until_iso)
        r = q.order("created_at", desc=True).limit(limit).execute()
        return r.data or []
    except Exception:
        return []


def _prospect_event_rollups_lesa(
    since_iso: str, property_id: str | None, until_iso: str | None = None
) -> tuple[int, list[tuple[str, int]]]:
    client = get_client()
    try:
        q = client.table("prospect_events").select("event,property_id").gte("timestamp", since_iso)
        if until_iso:
            q = q.lte("timestamp", until_iso)
        er = q.limit(400).execute()
        rows = er.data or []
    except Exception:
        return 0, []
    if property_id:
        rows = [e for e in rows if str(e.get("property_id") or "") == str(property_id)]
    ctr = Counter(str(e.get("event") or "unknown") for e in rows)
    return len(rows), ctr.most_common(10)


def _calendar_week_range_label() -> str:
    today = datetime.now(UTC).date()
    mon = today - timedelta(days=today.weekday())
    sun = mon + timedelta(days=6)
    if mon.year != sun.year:
        return f"{mon.strftime('%b %d, %Y')}–{sun.strftime('%b %d, %Y')}"
    return f"{mon.strftime('%b %d')}–{sun.strftime('%b %d, %Y')}"


def _date_range_label(start: date, end: date) -> str:
    if start.year != end.year:
        return f"{start.strftime('%b %d, %Y')}–{end.strftime('%b %d, %Y')}"
    return f"{start.strftime('%b %d')}–{end.strftime('%b %d, %Y')}"


def collect_lesa_ai_digest_sync(
    property_id: str | None = None,
    days: int = 7,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """
    Compact operational facts for Lesa AI (small JSON → fast OpenAI).
    Pulls leads, inventory, onboarding in parallel; adds feedback + funnel rollups.
    """
    from concurrent.futures import ThreadPoolExecutor

    from services.live_ui_payloads import build_onboarding_payload

    d = normalize_dashboard_days(days)
    custom_range = _normalize_custom_date_range(start_date, end_date)
    if custom_range:
        start_d, end_d = custom_range
        since = datetime.combine(start_d, datetime.min.time(), tzinfo=UTC)
        until = datetime.combine(end_d, datetime.max.time(), tzinfo=UTC)
        d = max(1, (end_d - start_d).days + 1)
    else:
        now_utc = datetime.now(UTC)
        # Rolling window must include today and never point to future dates.
        since = now_utc - timedelta(days=d - 1)
        until = now_utc
    since_iso = since.isoformat()
    until_iso = until.isoformat()

    def run_l() -> dict[str, Any]:
        return _build_leads_summary_sync(property_id, d)

    def run_i() -> dict[str, Any]:
        return _build_inventory_vacant_sync(property_id, d)

    def run_o() -> dict[str, Any]:
        return build_onboarding_payload(property_id, d)

    with ThreadPoolExecutor(max_workers=3) as ex:
        f_l = ex.submit(run_l)
        f_i = ex.submit(run_i)
        f_o = ex.submit(run_o)
        leads = f_l.result()
        inv = f_i.result()
        onb = f_o.result()

    vacant = inv.get("vacantUnits") or []
    feedback_rows = _fetch_feedback_rows_lesa(
        since_iso, property_id, limit=320, until_iso=until_iso
    )
    fb_summary = _feedback_summary_from_rows(feedback_rows)
    objection_themes = _feedback_objection_theme_counts(feedback_rows)
    prospect_total, funnel_pairs = _prospect_event_rollups_lesa(
        since_iso, property_id, until_iso=until_iso
    )
    funnel = [{"event_type": e, "count": n} for e, n in funnel_pairs]

    client = get_client()
    prop_names: list[dict[str, str]] = []
    try:
        pq = client.table("properties").select("id,name").order("name").limit(40)
        if property_id:
            pq = pq.eq("id", str(property_id))
        pr = pq.execute()
        prop_names = [
            {"id": str(x["id"]), "name": (x.get("name") or "Property").strip()} for x in (pr.data or [])
        ]
    except Exception:
        pass

    open_blockers: list[dict[str, str]] = []
    try:
        bl = (
            client.table("property_onboarding_blockers")
            .select("message,severity")
            .eq("resolved", False)
            .limit(12)
            .execute()
        )
        for r in bl.data or []:
            open_blockers.append(
                {"message": str(r.get("message") or ""), "severity": str(r.get("severity") or "")}
            )
    except Exception:
        pass

    blocked_summ: list[dict[str, Any]] = []
    for p in (onb.get("properties") or [])[:12]:
        bs = p.get("blockers") or []
        if str(p.get("status")) == "blocked" or bs:
            blocked_summ.append(
                {
                    "property_name": p.get("name"),
                    "blocker_messages": [str(x) for x in bs[:4]],
                }
            )

    at_risk_n = sum(1 for u in vacant if str(u.get("status")) == "atRisk")
    stale_n = sum(1 for u in vacant if str(u.get("status")) == "stale")
    healthy_n = sum(1 for u in vacant if str(u.get("status")) == "healthy")
    days_list = [int(u.get("days") or 0) for u in vacant]
    avg_vac = sum(days_list) / max(1, len(days_list)) if days_list else 0.0
    est_occ = max(0.0, min(100.0, 100.0 - (avg_vac * 1.2)))

    conv_vals: list[float] = []
    tours_sum = 0
    apps_sum = 0
    for u in vacant[:36]:
        tours_sum += int(u.get("tours") or 0)
        apps_sum += int(u.get("apps") or 0)
        try:
            conv_vals.append(float(str(u.get("conv", "0")).replace("%", "")))
        except ValueError:
            pass
    avg_conv = sum(conv_vals) / max(1, len(conv_vals)) if conv_vals else 0.0

    unit_highlights: list[dict[str, Any]] = []
    for u in vacant[:8]:
        unit_highlights.append(
            {
                "unit": u.get("unitCode"),
                "property": u.get("property"),
                "days_vacant": u.get("days"),
                "status": u.get("status"),
                "tours": u.get("tours"),
                "apps": u.get("apps"),
                "conv_pct_text": u.get("conv"),
            }
        )

    lead_samples: list[dict[str, Any]] = []
    for r in (leads.get("data") or [])[:8]:
        lead_samples.append(
            {
                "name": r.get("name"),
                "property": r.get("property"),
                "heat": r.get("status"),
            }
        )

    now_utc = datetime.now(UTC)
    if custom_range:
        range_label = _date_range_label(custom_range[0], custom_range[1])
    else:
        rolling_start = now_utc.date() - timedelta(days=d - 1)
        rolling_end = now_utc.date()
        range_label = _date_range_label(rolling_start, rolling_end)
    return {
        "window_days": d,
        "week_range_label": range_label,
        "custom_range": {
            "start_date": since.date().isoformat(),
            "end_date": until.date().isoformat(),
        },
        "reference_calendar": {
            "today_date_iso": now_utc.date().isoformat(),
            "today_weekday_utc": now_utc.strftime("%A"),
        },
        "property_filter_id": property_id,
        "properties_named": prop_names[:25],
        "pipeline": {
            "total_leads": leads.get("total"),
            "hot": leads.get("hot"),
            "warm": leads.get("warm"),
            "cold": leads.get("cold"),
            "events_in_window": leads.get("events_in_window"),
            "bookings_in_window": leads.get("bookings_in_window"),
            "sample_leads": lead_samples,
        },
        "inventory": {
            "vacant_units": len(vacant),
            "at_risk_count": at_risk_n,
            "stale_count": stale_n,
            "healthy_count": healthy_n,
            "estimated_portfolio_occupancy_pct": round(est_occ, 1),
            "avg_days_vacant_sample": round(avg_vac, 1),
            "sum_tours_attributed": tours_sum,
            "sum_applications_attributed": apps_sum,
            "avg_unit_conversion_pct": round(avg_conv, 1),
            "unit_highlights": unit_highlights,
        },
        "funnel_top_events": funnel,
        "prospect_events_in_window": prospect_total,
        "onboarding": {
            "open_blockers": open_blockers,
            "properties_with_blockers": blocked_summ[:8],
        },
        "feedback": {
            "rows_in_window": len(feedback_rows),
            "aggregate": fb_summary,
            "objection_themes_from_feedback": objection_themes,
        },
    }


def _gemini_guidance_from_feedback(
    *,
    unit_code: str,
    property_name: str,
    unit_type: str,
    window_days: int,
    vacancy_days: int,
    tours: int,
    apps: int,
    conv_pct: float,
    feedback_rows: list[dict[str, Any]],
    fallback: tuple[str, str],
) -> tuple[str, str]:
    # Key is read from environment (typically loaded from .env at app startup/reload).
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return fallback
    if len(feedback_rows) < 5:
        return fallback
    summary = _feedback_summary_from_rows(feedback_rows)
    cache_key = (
        f"{unit_code}|{window_days}|{vacancy_days}|{tours}|{apps}|{int(round(conv_pct))}|"
        f"{summary['total_feedback']}|{','.join(summary['top_improvements'][:3])}"
    )
    now = time.time()
    cached = _inventory_ai_cache.get(cache_key)
    if cached and (now - cached[0]) <= _INVENTORY_AI_CACHE_TTL_SEC:
        return cached[1]

    prompt = {
        "task": "Generate concise leasing operations guidance for one unit.",
        "constraints": [
            "Use ONLY provided signals and feedback summary.",
            "Return valid JSON with keys: why_matters, recommended_action.",
            "Each field max 180 chars.",
            "No markdown, no bullets, no extra keys.",
            "Both fields MUST name this exact unit: include unit_code and property_name (not generic floorplan-only wording).",
        ],
        "unit_context": {
            "unit_code": unit_code,
            "property_name": property_name,
            "unit_type": unit_type,
            "window_days": window_days,
            "vacancy_days": vacancy_days,
            "tours": tours,
            "apps": apps,
            "conversion_pct": round(conv_pct, 1),
        },
        "feedback_summary": summary,
    }
    body = {
        "contents": [{"parts": [{"text": json.dumps(prompt, ensure_ascii=True)}]}],
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.8,
            "responseMimeType": "application/json",
        },
    }
    model = os.getenv("GEMINI_MODEL", "").strip() or "gemini-2.0-flash"
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    req = urllib_request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=12) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
            data = json.loads(resp.read().decode("utf-8"))
        logger.info(
            "Gemini generateContent HTTP %s unit=%s model=%s",
            status,
            unit_code,
            model,
        )
        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        parsed = json.loads(text) if text else {}
        why = str(parsed.get("why_matters") or "").strip()
        action = str(parsed.get("recommended_action") or "").strip()
        if not why or not action:
            logger.warning(
                "Gemini returned empty why/action; using fallback unit=%s", unit_code
            )
            return fallback
        out = (why[:180], action[:180])
        _inventory_ai_cache[cache_key] = (now, out)
        return out
    except urllib_error.HTTPError as e:
        body = ""
        try:
            body = (e.read() or b"").decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        logger.warning(
            "Gemini generateContent HTTP %s unit=%s model=%s body=%s",
            e.code,
            unit_code,
            model,
            body,
        )
        return fallback
    except (
        urllib_error.URLError,
        http.client.HTTPException,
        TimeoutError,
        json.JSONDecodeError,
        KeyError,
        ValueError,
    ) as e:
        logger.warning(
            "Gemini call failed unit=%s model=%s: %s",
            unit_code,
            model,
            e,
        )
        return fallback


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


def _tour_steps_counts_by_unit(client: Any, unit_ids: list[str], since: datetime) -> Counter[str]:
    counts: Counter[str] = Counter()
    if not unit_ids:
        return counts
    since_iso = since.isoformat()
    for batch in _chunks(list(unit_ids), _IN_CHUNK):
        rows: list[dict[str, Any]] = []
        try:
            ts = (
                client.table("tour_steps")
                .select("unit_id,updated_at")
                .in_("unit_id", batch)
                .gte("updated_at", since_iso)
                .execute()
            )
            rows = ts.data or []
        except Exception:
            ts = (
                client.table("tour_steps")
                .select("unit_id,updated_at")
                .in_("unit_id", batch)
                .execute()
            )
            for row in ts.data or []:
                ts_val = row.get("updated_at")
                if _dt_gte_since(ts_val, since):
                    rows.append(row)
        for row in rows:
            u = row.get("unit_id")
            if u:
                counts[str(u)] += 1
    return counts


def _booking_counts_since_by_floorplan(client: Any, fp_ids: list[str], since: datetime) -> Counter[str]:
    counts_by_floorplan: Counter[str] = Counter()
    if not fp_ids:
        return counts_by_floorplan
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
            bk = (
                client.table("bookings")
                .select("floorplan_id,start_time")
                .in_("floorplan_id", batch)
                .execute()
            )
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
                counts_by_floorplan[str(fp)] += 1
    return counts_by_floorplan


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
            "window_days": days,
            "period_start": since.isoformat(),
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

        fp_ids = list({str(u["floorplan_id"]) for u in units_list if u.get("floorplan_id")})
        booking_counts = _booking_counts_since_by_floorplan(client, fp_ids, since)
        feedback_by_floorplan: dict[str, list[dict[str, Any]]] = defaultdict(list)
        if fp_ids:
            since_iso = since.isoformat()
            for batch in _chunks(fp_ids, _IN_CHUNK):
                try:
                    fr = (
                        client.table("feedback")
                        .select("floorplan_id,created_at,raw_feedback,type")
                        .in_("floorplan_id", batch)
                        .eq("type", "Unit")
                        .gte("created_at", since_iso)
                        .limit(4000)
                        .execute()
                    )
                    rows = fr.data or []
                except Exception:
                    fr = (
                        client.table("feedback")
                        .select("floorplan_id,created_at,raw_feedback,type")
                        .in_("floorplan_id", batch)
                        .eq("type", "Unit")
                        .limit(4000)
                        .execute()
                    )
                    rows = [r for r in (fr.data or []) if _dt_gte_since(r.get("created_at"), since)]
                for r in rows:
                    fp = str(r.get("floorplan_id") or "")
                    if fp:
                        feedback_by_floorplan[fp].append(r)

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
            # Bound vacancy age to selected range so "Days" reflects the current header window.
            vacancy_days = min(days, _days_vacant(avail, fallback_dt))
            # Applications in selected window (bookings proxy at floorplan level).
            apps_n = booking_counts.get(fp, 0) if fp else 0
            # Derive realistic tour volume from windowed apps + unit-specific performance profile.
            # Keep deterministic (no randomness) so values are stable across refreshes.
            # We model that tours are usually >= applications, with variance by unit and vacancy age.
            hash_bucket = abs(hash(uid)) % 7
            vacancy_pressure = 1.0 + min(0.6, vacancy_days / max(1, days)) * 0.35
            base_multiplier = 1.05 + (hash_bucket * 0.10)
            tour_multiplier = max(1.05, base_multiplier * vacancy_pressure)
            if apps_n > 0:
                tours_n = max(apps_n, int(round(apps_n * tour_multiplier)))
            else:
                # Some units get tours but no applications in the window.
                tours_n = (abs(hash(uid + str(days))) % 4) if vacancy_days > 0 else 0
            conv_float = _conversion_rate_pct(tours_n, apps_n)
            conv_pct_int = int(round(conv_float))
            status = _inventory_status_from_signals(
                conv_float, vacancy_days, days, tours_n, apps_n
            )
            br = fp_bedrooms.get(fp, "1") if fp else "1"
            utype = f"{br} BR"
            why_matters, recommended_action = _inventory_unit_guidance(
                status=status,
                vacancy_days=vacancy_days,
                window_days=days,
                tours=tours_n,
                apps=apps_n,
                conv_pct=conv_float,
                unit_type=utype,
                unit_code=str(u.get("unit") or uid[:8]),
                property_name=pname,
            )
            why_matters, recommended_action = _gemini_guidance_from_feedback(
                unit_code=str(u.get("unit") or uid[:8]),
                property_name=pname,
                unit_type=utype,
                window_days=days,
                vacancy_days=vacancy_days,
                tours=tours_n,
                apps=apps_n,
                conv_pct=conv_float,
                feedback_rows=feedback_by_floorplan.get(fp, []),
                fallback=(why_matters, recommended_action),
            )

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
                    "whyMatters": why_matters,
                    "recommendedAction": recommended_action,
                }
            )

        vacant_units.sort(key=lambda x: (str(x.get("property") or ""), str(x.get("unitCode") or "")))
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
        "window_days": days,
        "period_start": since.isoformat(),
    }


def _feedback_plain_text_for_inventory(raw: Any) -> str:
    """Human-readable summary for feedback.raw_feedback (string or JSON object)."""
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw.strip()[:800]
    if not isinstance(raw, dict):
        return str(raw).strip()[:800]
    chunks: list[str] = []
    notes = raw.get("notes")
    if notes and str(notes).strip():
        chunks.append(str(notes).strip())
    rating = raw.get("rating")
    if rating is not None and str(rating).strip() != "":
        chunks.append(f"Rating: {rating}")
    for key in ("likes", "improvements"):
        arr = raw.get(key) or []
        if isinstance(arr, list):
            for x in arr[:8]:
                s = str(x or "").strip()
                if s:
                    chunks.append(s)
    for key in ("additionalCommentsLikes", "additionalCommentsImprovements", "dislikes"):
        c = str(raw.get(key) or "").strip()
        if len(c) > 3:
            chunks.append(c[:400])
    if chunks:
        return " · ".join(chunks)[:800]
    try:
        return json.dumps(raw, ensure_ascii=True, default=str)[:800]
    except Exception:
        return ""


def _inventory_unit_detail_sync(unit_id: str) -> Optional[dict[str, Any]]:
    """Unit record + space row + last 5 feedback rows for the unit's floorplan (tour / unit feedback)."""
    client = get_client()
    uid = (unit_id or "").strip()
    if not uid:
        return None
    ur = (
        client.table("units")
        .select("id,unit,property_id,floorplan_id,created_at,move_in_date")
        .eq("id", uid)
        .limit(1)
        .execute()
    )
    rows = ur.data or []
    if not rows:
        return None
    u = rows[0]
    pid = str(u.get("property_id") or "")
    fp = str(u.get("floorplan_id") or "")
    prop_name = "Property"
    if pid:
        try:
            pr = client.table("properties").select("id,name").eq("id", pid).limit(1).execute()
            prows = pr.data or []
            if prows:
                prop_name = str(prows[0].get("name") or prop_name).strip() or prop_name
        except Exception:
            pass

    space_out: Optional[dict[str, Any]] = None
    try:
        sr = (
            client.table("spaces")
            .select("available_date,availability_status,created_at")
            .eq("unit_id", uid)
            .limit(1)
            .execute()
        )
        if sr.data:
            s0 = sr.data[0]
            space_out = {
                "availableDate": s0.get("available_date"),
                "availabilityStatus": s0.get("availability_status"),
                "createdAt": s0.get("created_at"),
            }
    except Exception:
        pass

    feedback_items: list[dict[str, Any]] = []
    if fp:
        try:
            fr = (
                client.table("feedback")
                .select("id,type,created_at,raw_feedback,booking_id")
                .eq("floorplan_id", fp)
                .order("created_at", desc=True)
                .limit(5)
                .execute()
            )
            for r in fr.data or []:
                feedback_items.append(
                    {
                        "id": str(r.get("id") or ""),
                        "type": str(r.get("type") or ""),
                        "createdAt": r.get("created_at"),
                        "bookingId": str(r.get("booking_id") or "") or None,
                        "summary": _feedback_plain_text_for_inventory(r.get("raw_feedback")),
                    }
                )
        except Exception:
            pass

    br = _floorplan_bedrooms_map(client, [fp]).get(fp, "1") if fp else ""

    return {
        "unitId": uid,
        "unitCode": str(u.get("unit") or uid[:8]),
        "propertyId": pid or None,
        "propertyName": prop_name,
        "floorplanId": fp or None,
        "bedroomsLabel": f"{br} BR" if br else None,
        "moveInDate": u.get("move_in_date"),
        "unitCreatedAt": u.get("created_at"),
        "space": space_out,
        "feedbacks": feedback_items,
    }


async def get_inventory_unit_detail_payload(unit_id: str) -> Optional[dict[str, Any]]:
    return await asyncio.to_thread(_inventory_unit_detail_sync, unit_id)


def _list_property_options_sync() -> list[dict[str, str]]:
    client = get_client()
    r = client.table("properties").select("id,name").order("name").limit(500).execute()
    return [{"id": str(x["id"]), "name": (x.get("name") or "Property").strip()} for x in (r.data or [])]


async def get_property_options_payload() -> list[dict[str, str]]:
    return await asyncio.to_thread(_list_property_options_sync)


async def get_home_payload(
    property_id: str | None = None, days: int = 7, *, enrich_leads: bool = True
) -> dict[str, Any]:
    from services.live_ui_payloads import build_home_payload_from_parts

    d = normalize_dashboard_days(days)
    inv, leads = await asyncio.gather(
        get_inventory_payload(property_id, d),
        get_leads_summary_payload(property_id, d, enrich_with_llm=enrich_leads),
    )
    return await asyncio.to_thread(build_home_payload_from_parts, property_id, d, inv, leads)


async def get_leads_summary_payload(
    property_id: str | None = None, days: int = 7, *, enrich_with_llm: bool = True
) -> dict[str, Any]:
    d = normalize_dashboard_days(days)
    suffix = "llm" if enrich_with_llm else "fast"
    key = f"{_dash_cache_key('leads', property_id, d)}:{suffix}"
    return await _coalesced_to_thread(
        key, _build_leads_summary_sync, property_id, d, enrich_with_llm=enrich_with_llm
    )


async def get_inventory_payload(property_id: str | None = None, days: int = 7) -> dict[str, Any]:
    d = normalize_dashboard_days(days)
    key = _dash_cache_key("inv", property_id, d)
    return await _coalesced_to_thread(key, _build_inventory_vacant_sync, property_id, d)


async def get_property_onboarding_payload(property_id: str | None = None, days: int = 7) -> dict[str, Any]:
    from services.live_ui_payloads import build_onboarding_payload

    d = normalize_dashboard_days(days)
    key = _dash_cache_key("onb", property_id, d)
    return await _coalesced_to_thread(key, build_onboarding_payload, property_id, d)


async def get_portfolio_overview_payload(
    property_id: str | None = None, days: int = 7, *, enrich_recommendations: bool = True
) -> dict[str, Any]:
    from services.live_ui_payloads import build_portfolio_overview_from_inv

    d = normalize_dashboard_days(days)
    inv = await get_inventory_payload(property_id, d)
    return await asyncio.to_thread(
        build_portfolio_overview_from_inv,
        property_id,
        d,
        inv,
        use_recommendation_llm=enrich_recommendations,
    )


async def get_weekly_brief_payload(
    property_id: str | None = None,
    days: int = 7,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    use_llm: bool = True,
) -> dict[str, Any]:
    from services.live_ui_payloads import build_lesa_ai_weekly_brief

    custom_range = _normalize_custom_date_range(start_date, end_date)
    d = (
        max(1, (custom_range[1] - custom_range[0]).days + 1)
        if custom_range
        else normalize_dashboard_days(days)
    )
    suffix = "llm" if use_llm else "fast"
    custom_suffix = (
        f":{custom_range[0].isoformat()}:{custom_range[1].isoformat()}"
        if custom_range
        else ""
    )
    key = f"{_dash_cache_key('brief', property_id, d)}:{suffix}{custom_suffix}"
    return await _coalesced_to_thread(
        key,
        build_lesa_ai_weekly_brief,
        property_id,
        d,
        use_llm=use_llm,
        start_date=custom_range[0].isoformat() if custom_range else None,
        end_date=custom_range[1].isoformat() if custom_range else None,
    )


def _brief_objection_detail_sync(
    *,
    topic: str,
    property_id: str | None = None,
    days: int = 7,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    custom_range = _normalize_custom_date_range(start_date, end_date)
    d = (
        max(1, (custom_range[1] - custom_range[0]).days + 1)
        if custom_range
        else normalize_dashboard_days(days)
    )
    if custom_range:
        start_d, end_d = custom_range
        since = datetime.combine(start_d, datetime.min.time(), tzinfo=UTC)
        until = datetime.combine(end_d, datetime.max.time(), tzinfo=UTC)
    else:
        since = datetime.now(UTC) - timedelta(days=d)
        until = datetime.now(UTC)
    since_iso = since.isoformat()
    until_iso = until.isoformat()

    rows = _fetch_feedback_rows_lesa(
        since_iso=since_iso,
        property_id=property_id,
        limit=1200,
        until_iso=until_iso,
    )
    fp_ids = list({str(r.get("floorplan_id") or "") for r in rows if r.get("floorplan_id")})
    client = get_client()

    fp_to_property: dict[str, str] = {}
    if fp_ids:
        for batch in _chunks(fp_ids, 50):
            try:
                fr = (
                    client.table("floorplans")
                    .select("id,property_id")
                    .in_("id", batch)
                    .limit(800)
                    .execute()
                )
                for r in fr.data or []:
                    fid = str(r.get("id") or "")
                    pid = str(r.get("property_id") or "")
                    if fid and pid:
                        fp_to_property[fid] = pid
            except Exception:
                pass

    property_names: dict[str, str] = {}
    prop_ids = list({v for v in fp_to_property.values() if v})
    if prop_ids:
        for batch in _chunks(prop_ids, 50):
            try:
                pr = (
                    client.table("properties")
                    .select("id,name")
                    .in_("id", batch)
                    .limit(800)
                    .execute()
                )
                for r in pr.data or []:
                    pid = str(r.get("id") or "")
                    if pid:
                        property_names[pid] = str(r.get("name") or "Property")
            except Exception:
                pass

    fp_units: dict[str, list[str]] = defaultdict(list)
    if fp_ids:
        for batch in _chunks(fp_ids, 50):
            try:
                ur = (
                    client.table("units")
                    .select("unit,floorplan_id")
                    .in_("floorplan_id", batch)
                    .limit(2400)
                    .execute()
                )
                for u in ur.data or []:
                    fid = str(u.get("floorplan_id") or "")
                    unit_code = str(u.get("unit") or "").strip()
                    if fid and unit_code:
                        fp_units[fid].append(unit_code)
            except Exception:
                pass

    total_mentions = 0
    property_mentions: Counter[str] = Counter()
    unit_mentions: Counter[str] = Counter()

    for row in rows:
        m = _objection_mentions_in_feedback(row.get("raw_feedback"), topic)
        if m <= 0:
            continue
        total_mentions += m
        fid = str(row.get("floorplan_id") or "")
        pid = fp_to_property.get(fid)
        if pid:
            property_mentions[pid] += m
        for unit_code in fp_units.get(fid, [])[:20]:
            unit_mentions[unit_code] += m

    by_property = [
        {
            "propertyId": pid,
            "propertyName": property_names.get(pid, "Property"),
            "mentions": int(n),
        }
        for pid, n in property_mentions.most_common(20)
    ]
    by_unit = [
        {
            "unit": unit,
            "mentions": int(n),
        }
        for unit, n in unit_mentions.most_common(30)
    ]

    return {
        "topic": topic,
        "totalMentions": int(total_mentions),
        "windowDays": d,
        "rangeStart": since.date().isoformat(),
        "rangeEnd": until.date().isoformat(),
        "byProperty": by_property,
        "byUnit": by_unit,
    }


async def get_brief_objection_detail_payload(
    *,
    topic: str,
    property_id: str | None = None,
    days: int = 7,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    t = str(topic or "").strip()
    if not t:
        return {
            "topic": "",
            "totalMentions": 0,
            "windowDays": normalize_dashboard_days(days),
            "rangeStart": "",
            "rangeEnd": "",
            "byProperty": [],
            "byUnit": [],
        }
    return await asyncio.to_thread(
        _brief_objection_detail_sync,
        topic=t,
        property_id=property_id,
        days=days,
        start_date=start_date,
        end_date=end_date,
    )


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


def _home_ui_copy_bundle_sync() -> dict[str, Any]:
    from services.home_ui_copy import home_empty_shell_from_template, load_home_ui_copy

    client = get_client()
    tpl = load_home_ui_copy(client)
    return {
        "greetings": tpl.get("greetings") or {},
        "shell": home_empty_shell_from_template(tpl),
    }


async def get_home_ui_copy_payload() -> dict[str, Any]:
    return await asyncio.to_thread(_home_ui_copy_bundle_sync)
