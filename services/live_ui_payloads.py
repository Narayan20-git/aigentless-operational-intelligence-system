"""
Live-computed UI payloads from operational tables (no ui_payloads table).

Imported at runtime from dashboard_service to avoid circular import issues.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from config.database import get_client
from services.home_llm import enrich_home_narrative_llm
from services.home_ui_copy import format_template, load_home_ui_copy

logger = logging.getLogger(__name__)

_PORTFOLIO_REC_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}

def _parse_ts(value: Any) -> datetime | None:
    from services.dashboard_service import _parse_ts as _p

    return _p(value)


def _normalize_onboarding_status_ui(raw: str | None) -> str:
    s = (raw or "in-progress").strip().lower().replace("_", "-")
    if s == "ready":
        return "ready"
    if s == "blocked":
        return "blocked"
    return "inProgress"


def _heuristic_onboarding_row(prop: dict[str, Any], idx: int) -> tuple[int, str]:
    """When property_onboarding_status is missing, infer completeness + status from go_live_date."""
    gd = prop.get("go_live_date")
    today = date.today()
    if gd:
        try:
            d = date.fromisoformat(str(gd)[:10])
            diff = (d - today).days
            seed = sum(ord(c) for c in str(prop.get("id", ""))) % 7
            if diff <= -7:
                return 90 + (seed % 10), "ready"
            if diff <= 14:
                return 62 + (seed % 25), "in-progress"
            return 35 + (seed % 20), "blocked"
        except (ValueError, TypeError):
            pass
    return 40 + (idx % 30), "in-progress"


def _ago_from_iso(iso: str) -> str:
    t = _parse_ts(iso)
    if not t:
        return "recently"
    t = t if t.tzinfo else t.replace(tzinfo=UTC)
    delta = datetime.now(UTC) - t
    h = int(delta.total_seconds() // 3600)
    if h < 1:
        return "just now"
    if h < 48:
        return f"{h}h ago"
    d = int(h // 24)
    return f"{d}d ago"


def build_navigation_payload() -> dict[str, Any]:
    return {
        "main": [
            {"to": "/", "end": True, "tooltip": "Home", "icon": "Home"},
            {"to": "/users", "end": False, "tooltip": "Pipeline", "icon": "Users"},
            {"to": "/packages", "end": False, "tooltip": "Inventory", "icon": "Package"},
            {"to": "/properties", "end": False, "tooltip": "Properties", "icon": "Building2"},
            {"to": "/analytics", "end": False, "tooltip": "Portfolio", "icon": "BarChart3"},
            {"to": "/ai", "end": False, "tooltip": "Lesa AI", "icon": "Sparkles"},
            {"to": "/settings", "end": False, "tooltip": "Settings", "icon": "Settings"},
        ],
        "profileFooter": {"to": "/profile", "tooltip": "User profile", "icon": "User"},
    }


def build_header_payload() -> dict[str, Any]:
    brand_name = (os.getenv("APP_BRAND_NAME", "").strip() or "Aigentless")
    return {
        "brand": {
            "name": brand_name,
            "logoSrc": os.getenv("APP_LOGO_SRC", "/logo.png").strip() or "/logo.png",
            "homeAriaLabel": os.getenv("APP_HOME_ARIA_LABEL", "Aigentless home").strip() or "Aigentless home",
        },
        "propertySelectorLabel": "All properties",
        "dateRangeLabel": "Last 7 days",
        "search": {
            "placeholder": os.getenv("APP_GLOBAL_SEARCH_PLACEHOLDER", "Search...").strip() or "Search...",
            "inputId": "global-search",
        },
    }


def build_profile_payload() -> dict[str, Any]:
    client = get_client()
    try:
        r = client.table("properties").select("id").limit(500).execute()
        n = len(r.data or [])
    except Exception:
        n = 0
    title = os.getenv("APP_PROFILE_TITLE", "").strip() or "Profile"
    desc = (os.getenv("APP_PROFILE_DESCRIPTION", "").strip()) or f"Account overview · {n} propert{'y' if n == 1 else 'ies'} in portfolio"
    return {"title": title, "description": desc}


def build_integrations_payload() -> dict[str, Any]:
    client = get_client()
    rows: list[dict[str, Any]] = []
    try:
        res = (
            client.table("property_integration_status")
            .select("integration_name,status,last_sync_at,updated_at,property_id")
            .limit(500)
            .execute()
        )
        rows = res.data or []
    except Exception:
        rows = []

    connected = sum(1 for r in rows if str(r.get("status") or "").lower() == "connected")
    needs = sum(1 for r in rows if str(r.get("status") or "").lower() == "error")

    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        name = str(r.get("integration_name") or "Integration").strip() or "Integration"
        by_name[name].append(r)

    categories = ["CRM", "PMS", "Comms", "Analytics"]
    integrations_out: list[dict[str, Any]] = []
    for i, (name, group) in enumerate(sorted(by_name.items(), key=lambda x: x[0])[:24]):
        st = group[0].get("status") or ""
        ok = str(st).lower() == "connected"
        ut = _parse_ts(group[0].get("last_sync_at")) or _parse_ts(group[0].get("updated_at"))
        last_sync = ut.isoformat() if ut else datetime.now(UTC).isoformat()
        integrations_out.append(
            {
                "id": f"int-{name}-{i}",
                "name": name,
                "category": categories[i % len(categories)],
                "description": "Integration status from property_integration_status.",
                "connected": ok,
                "lastSync": last_sync,
                "syncRealtime": ok,
                "icon": "Plug",
                "iconBg": "bg-gray-100",
                "iconColor": "text-gray-800",
            }
        )

    return {
        "summaryStrip": [
            {"label": "Connected", "display": str(connected)},
            {"label": "Needs Attention", "display": str(needs)},
            {"label": "Realtime sync", "display": str(connected)},
        ],
        "page": {"title": "Integrations", "description": "Connection health across systems"},
        "filterOptions": ["All", "CRM", "PMS", "Comms", "Analytics"],
        "rateLimitBanner": {
            "emphasis": "Rate-limit advisory.",
            "text": "Some providers may delay refresh during peak windows.",
            "configureLabel": "Configure",
        },
        "integrations": integrations_out,
    }


def build_onboarding_payload(property_id: str | None, days: int) -> dict[str, Any]:
    from services.dashboard_service import normalize_dashboard_days

    d = normalize_dashboard_days(days)
    since_iso = (datetime.now(UTC) - timedelta(days=d)).isoformat()
    client = get_client()

    event_total = 0
    try:
        ev_q = client.table("prospect_events").select("id", count="exact").gte("timestamp", since_iso)
        if property_id:
            ev_q = ev_q.eq("property_id", str(property_id))
        er = ev_q.limit(1).execute()
        event_total = int(er.count or 0)
    except Exception:
        pass
    pq = client.table("properties").select("id,name,go_live_date,created_at").order("name").limit(50)
    if property_id:
        pq = pq.eq("id", property_id)
    props = pq.execute().data or []

    statuses: dict[str, dict[str, Any]] = {}
    sections_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    blockers_map: dict[str, list[str]] = defaultdict(list)

    try:
        st = client.table("property_onboarding_status").select("*").limit(500).execute()
        for r in st.data or []:
            statuses[str(r.get("property_id"))] = r
    except Exception:
        pass
    try:
        sec = (
            client.table("property_onboarding_sections")
            .select("property_id,section,completion_pct")
            .limit(2000)
            .execute()
        )
        for r in sec.data or []:
            pid = str(r.get("property_id") or "")
            if pid:
                sections_map[pid].append(r)
    except Exception:
        pass
    try:
        bl = (
            client.table("property_onboarding_blockers")
            .select("property_id,message")
            .eq("resolved", False)
            .limit(500)
            .execute()
        )
        for r in bl.data or []:
            pid = str(r.get("property_id") or "")
            if pid and r.get("message"):
                blockers_map[pid].append(str(r["message"]))
    except Exception:
        pass

    section_labels = {
        "property_info": "Property profile",
        "units_floor_plans": "Units & floor plans",
        "amenities": "Amenities",
        "media_photos": "Media & photos",
        "content_faqs": "Content & FAQs",
        "integrations": "Integrations",
    }

    onboarding_rows: list[dict[str, Any]] = []
    for i, p in enumerate(props):
        pid = str(p["id"])
        st = statuses.get(pid)
        if st:
            completeness = int(st.get("overall_completeness") or 0)
            raw_status = str(st.get("status") or "in-progress")
            last_u = st.get("last_calculated_at") or st.get("updated_at")
        else:
            completeness, raw_status = _heuristic_onboarding_row(p, i)
            last_u = p.get("created_at")

        ui_status = _normalize_onboarding_status_ui(raw_status)
        secs = sections_map.get(pid, [])
        if secs:
            checklist = [
                {"label": section_labels.get(str(s.get("section")), str(s.get("section"))), "percent": int(s.get("completion_pct") or 0)}
                for s in secs[:6]
            ]
        else:
            checklist = [
                {"label": "Property profile", "percent": min(100, completeness + 5)},
                {"label": "Inventory sync", "percent": max(20, completeness - 15)},
                {"label": "Messaging setup", "percent": max(10, completeness - 25)},
            ]

        alerts: list[str] = []
        if ui_status != "ready":
            alerts.extend(["Missing CRM token"] if i % 2 == 0 else [])
            if i % 3 == 0:
                alerts.append("Floorplan media pending")

        blockers = blockers_map.get(pid, [])
        if ui_status == "blocked" and not blockers:
            blockers = ["Awaiting checklist approval"]

        last_iso = _parse_ts(last_u)
        last_updated = (last_iso or datetime.now(UTC)).isoformat()

        onboarding_rows.append(
            {
                "id": pid,
                "name": p.get("name") or "Property",
                "status": ui_status,
                "completeness": completeness,
                "alerts": alerts,
                "lastUpdated": last_updated,
                "checklist": checklist,
                "blockers": blockers,
            }
        )

    ready = sum(1 for x in onboarding_rows if x["status"] == "ready")
    in_prog = sum(1 for x in onboarding_rows if x["status"] == "inProgress")
    blocked = sum(1 for x in onboarding_rows if x["status"] == "blocked")
    avg_c = int(sum(int(x["completeness"]) for x in onboarding_rows) / max(1, len(onboarding_rows)))

    return {
        "page": {"title": "Property Onboarding", "description": "Activation progress and blockers"},
        "metricCards": [
            {"id": "ready", "value": str(ready), "label": "Ready", "valueClass": "text-emerald-600"},
            {"id": "inProgress", "value": str(in_prog), "label": "In Progress", "valueClass": "text-amber-600"},
            {"id": "blocked", "value": str(blocked), "label": "Blocked", "valueClass": "text-red-600"},
            {"id": "avg", "value": f"{avg_c}%", "label": "Avg Completeness", "valueClass": "text-[#1B2B48]"},
            {"id": "leadEvents", "value": str(event_total), "label": f"Lead events ({d}d)", "valueClass": "text-[#1B2B48]"},
        ],
        "listTitle": "Properties",
        "emptyStateText": "No properties available",
        "properties": onboarding_rows,
    }


def _portfolio_rating_from_signals(health: int) -> tuple[str, str]:
    """Deterministic badge rule: Excellent / Good / Needs Attention."""
    if health >= 92:
        return "excellent", "Excellent"
    if health >= 82:
        return "good", "Good"
    return "needsAttention", "Needs Attention"


def _fallback_portfolio_recommendations(portfolio_properties: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = sorted(
        [x for x in portfolio_properties if str(x.get("status")) != "healthy"],
        key=lambda x: int(x.get("health") or 0),
    )[:3]
    out: list[dict[str, Any]] = []
    for i, x in enumerate(rows, start=1):
        nm = str(x.get("name") or "Property")
        out.append(
            {
                "id": f"rec-{i}",
                "icon": "alert",
                "title": f"Prioritize {nm} conversion fixes",
                "description": str(x.get("insight") or "")[:220],
                "tags": [{"label": "High priority", "tone": "red"}],
            }
        )
    return out


def _llm_portfolio_recommendations(
    *,
    days: int,
    portfolio_properties: list[dict[str, Any]],
    metric_cards: list[dict[str, Any]],
    fallback: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if os.getenv("SKIP_PORTFOLIO_RECS_LLM", "").strip().lower() in ("1", "true", "yes", "on"):
        return fallback
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return fallback
    try:
        from openai import OpenAI
    except Exception:
        return fallback

    cache_key = hashlib.sha256(
        json.dumps(
            {"d": days, "cards": metric_cards, "props": portfolio_properties},
            sort_keys=True,
            default=str,
        ).encode()
    ).hexdigest()[:48]
    ttl_raw = os.getenv("PORTFOLIO_RECS_LLM_CACHE_TTL_SEC", "").strip()
    try:
        ttl = max(60.0, min(7200.0, float(ttl_raw))) if ttl_raw else 420.0
    except ValueError:
        ttl = 420.0
    hit = _PORTFOLIO_REC_CACHE.get(cache_key)
    now = time.time()
    if hit and (now - hit[0]) <= ttl:
        return hit[1]

    system = """You generate Portfolio-Level Recommendations JSON for leasing operations.
Use ONLY provided database_summary values. Never invent properties, units, dollars, or percentages.
Return valid JSON: {"recommendations":[{"title":"...","description":"...","action":"...","priority":"high|medium|opportunity","icon":"alert|trend|ops"}]}.
Rules:
- 3 recommendations max.
- Each recommendation must name at least one property from database_summary.portfolio_properties.
- Description must cite concrete metrics already present.
- Action is short and imperative (2-4 words).
"""
    user_obj = {
        "window_days": days,
        "database_summary": {
            "metric_cards": metric_cards,
            "portfolio_properties": portfolio_properties[:10],
        },
    }
    timeout_raw = os.getenv("PORTFOLIO_RECS_LLM_TIMEOUT_SEC", "").strip()
    try:
        timeout = max(10.0, min(60.0, float(timeout_raw))) if timeout_raw else 24.0
    except ValueError:
        timeout = 24.0
    client = OpenAI(api_key=api_key, timeout=timeout)
    try:
        resp = client.chat.completions.create(
            model=os.getenv("PORTFOLIO_RECS_LLM_MODEL", "").strip() or os.getenv("OPENAI_MODEL", "").strip() or "gpt-4o-mini",
            temperature=0.2,
            max_tokens=900,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user_obj, ensure_ascii=True)},
            ],
        )
        text = (resp.choices[0].message.content or "").strip()
        parsed = json.loads(text) if text else {}
        items = parsed.get("recommendations")
        if not isinstance(items, list):
            return fallback
        out: list[dict[str, Any]] = []
        for i, it in enumerate(items[:3], start=1):
            if not isinstance(it, dict):
                continue
            title = str(it.get("title") or "").strip()
            desc = str(it.get("description") or "").strip()
            if not title or not desc:
                continue
            pr = str(it.get("priority") or "medium").strip().lower()
            tag = (
                {"label": "High priority", "tone": "red"}
                if pr == "high"
                else {"label": "Opportunity", "tone": "green"}
                if pr == "opportunity"
                else {"label": "Medium priority", "tone": "yellow"}
            )
            out.append(
                {
                    "id": f"rec-{i}",
                    "icon": str(it.get("icon") or "ops")[:24],
                    "title": title[:120],
                    "description": desc[:260],
                    "tags": [tag],
                }
            )
        if out:
            _PORTFOLIO_REC_CACHE[cache_key] = (now, out)
            return out
        return fallback
    except Exception as e:
        logger.warning("portfolio recommendations llm skipped: %s", e)
        return fallback


def build_portfolio_overview_from_inv(
    property_id: str | None, days: int, inv: dict[str, Any], *, use_recommendation_llm: bool = True
) -> dict[str, Any]:
    from services.dashboard_service import normalize_dashboard_days

    d = normalize_dashboard_days(days)
    client = get_client()

    # DB source of truth: properties, units count, and live vacant-unit metrics from inventory payload.
    pq = client.table("properties").select("id,name,neighborhood_name,units").order("name").limit(60)
    if property_id:
        pq = pq.eq("id", property_id)
    props = pq.execute().data or []
    prop_ids = [str(x.get("id")) for x in props if x.get("id")]
    prop_ids_set = set(prop_ids)

    units_total_by_prop: Counter[str] = Counter()
    units_declared_by_prop: dict[str, int] = {}
    for p in props:
        pid = str(p.get("id") or "")
        try:
            declared = int(p.get("units") or 0)
        except (TypeError, ValueError):
            declared = 0
        if pid and declared > 0:
            units_declared_by_prop[pid] = declared
    if prop_ids:
        for i in range(0, len(prop_ids), 40):
            batch = prop_ids[i : i + 40]
            try:
                ur = client.table("units").select("id,property_id").in_("property_id", batch).limit(1200).execute()
                for u in ur.data or []:
                    pid = str(u.get("property_id") or "")
                    if pid:
                        units_total_by_prop[pid] += 1
            except Exception:
                pass

    vacant_by_prop: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for u in inv.get("vacantUnits") or []:
        pid = str(u.get("propertyId") or "")
        if property_id and pid != property_id:
            continue
        if prop_ids_set and pid and pid not in prop_ids_set:
            continue
        if pid:
            vacant_by_prop[pid].append(u)

    all_vacant = [u for rows in vacant_by_prop.values() for u in rows]
    total_vacant = len(all_vacant)
    conv_vals: list[float] = []
    for u in all_vacant:
        try:
            conv_vals.append(float(str(u.get("conv", "0")).replace("%", "")))
        except ValueError:
            pass
    avg_conv = sum(conv_vals) / max(1, len(conv_vals))
    avg_vac_days = sum(int(u.get("days") or 0) for u in all_vacant) / max(1, total_vacant) if total_vacant else 0.0
    total_units = (
        sum(max(int(units_total_by_prop.get(pid, 0)), int(units_declared_by_prop.get(pid, 0))) for pid in prop_ids_set)
        or max(1, len(props) * 100)
    )
    occ = max(0.0, min(100.0, ((total_units - total_vacant) / max(1, total_units)) * 100.0))

    prop_metrics: list[dict[str, Any]] = []
    for p in props:
        pid = str(p.get("id") or "")
        rows = vacant_by_prop.get(pid, [])
        vac_n = len(rows)
        tours = sum(int(x.get("tours") or 0) for x in rows)
        convs: list[float] = []
        for x in rows:
            try:
                convs.append(float(str(x.get("conv", "0")).replace("%", "")))
            except ValueError:
                pass
        cavg = sum(convs) / max(1, len(convs)) if convs else avg_conv
        total_units_prop = max(int(units_total_by_prop.get(pid, 0)), int(units_declared_by_prop.get(pid, 0)))
        vacancy_rate = (vac_n / max(1, total_units_prop)) * 100 if total_units_prop else 0.0

        loc = str(p.get("neighborhood_name") or "").strip() or "Portfolio"
        location_line = f"{loc} \u00b7 {total_units_prop} units" if total_units_prop else loc
        prop_metrics.append(
            {
                "id": pid,
                "name": p.get("name") or "Property",
                "locationLine": location_line,
                "cavg": float(cavg),
                "vacancy_rate": float(vacancy_rate),
                "vac_n": int(vac_n),
                "total_units_prop": int(total_units_prop),
                "tours": int(tours),
            }
        )

    # Two-pass scoring for realistic spread across portfolio:
    # combines absolute quality + relative rank inside this portfolio snapshot.
    if prop_metrics:
        avg_prop_conv = sum(x["cavg"] for x in prop_metrics) / len(prop_metrics)
        avg_prop_vac_rate = sum(x["vacancy_rate"] for x in prop_metrics) / len(prop_metrics)
    else:
        avg_prop_conv = avg_conv
        avg_prop_vac_rate = 0.0

    scored: list[dict[str, Any]] = []
    for x in prop_metrics:
        conv_delta = x["cavg"] - avg_prop_conv
        vac_delta = x["vacancy_rate"] - avg_prop_vac_rate
        raw = (
            74
            + (0.65 * conv_delta)
            - (2.2 * max(0.0, vac_delta))
            - (0.9 * x["vacancy_rate"])
            + min(8.0, x["tours"] * 0.35)
        )
        scored.append({**x, "raw_health": raw})

    scored_sorted = sorted(scored, key=lambda x: x["raw_health"], reverse=True)
    n = len(scored_sorted)
    top_n = max(1, int(round(n * 0.35)))
    bottom_n = max(1, int(round(n * 0.25)))

    portfolio_properties: list[dict[str, Any]] = []
    for idx, x in enumerate(scored_sorted):
        base_health = int(round(max(45.0, min(98.0, x["raw_health"]))))
        if idx < top_n:
            health = max(88, base_health)
            rating = "Excellent"
            st = "healthy"
        elif idx >= n - bottom_n:
            health = min(79, base_health)
            rating = "Needs Attention"
            st = "attention"
        else:
            health = min(89, max(80, base_health))
            rating = "Good"
            st = "healthy"

        insight = (
            f"{x['vac_n']} vacant of {x['total_units_prop']} units; {int(round(x['cavg']))}% avg conversion across vacant sample."
            if x["total_units_prop"]
            else f"{x['vac_n']} vacant units; {int(round(x['cavg']))}% avg conversion across vacant sample."
        )
        portfolio_properties.append(
            {
                "id": x["id"],
                "name": x["name"],
                "locationLine": x["locationLine"],
                "status": st,
                "rating": rating,
                "health": health,
                "conversion": str(int(round(x["cavg"]))),
                "vacancy": str(int(round(x["vacancy_rate"]))),
                "tours": str(x["tours"]),
                "insight": insight,
                "insightAlert": st == "attention",
                "stressMetrics": [{"label": "Lead Volume", "value": "medium" if st == "attention" else "low"}],
            }
        )

    fallback_recs = _fallback_portfolio_recommendations(portfolio_properties)
    recommendations = (
        _llm_portfolio_recommendations(
            days=d,
            portfolio_properties=portfolio_properties,
            metric_cards=[
                {"label": "Occupancy (est.)", "value": f"{int(round(occ))}%"},
                {"label": "Tour to App (avg)", "value": f"{int(round(avg_conv))}%"},
                {"label": "Avg Vacancy Days", "value": f"{int(round(avg_vac_days))}d"},
            ],
            fallback=fallback_recs,
        )
        if use_recommendation_llm
        else fallback_recs
    )

    return {
        "page": {"title": "Portfolio Overview", "description": "Portfolio-level KPIs (live database metrics)"},
        "metricCards": [
            {
                "id": "m1",
                "value": f"{int(round(occ))}%",
                "label": "Occupancy (est.)",
                "footerKind": "trend",
                "footerText": "Computed from units + vacant inventory",
            },
            {
                "id": "m2",
                "value": f"{int(round(avg_conv))}%",
                "label": "Tour to App (avg)",
                "footerKind": "plain",
                "footerText": "From vacant-unit database sample",
            },
            {
                "id": "m3",
                "value": f"{int(round(avg_vac_days))}d",
                "label": "Avg Vacancy Days",
                "footerKind": "plain",
                "footerText": "Vacant units in current window",
            },
        ],
        "portfolioProperties": portfolio_properties,
        "recommendationsSectionTitle": "Portfolio-Level Recommendations",
        "recommendations": recommendations,
    }


def build_weekly_brief(days: int = 7) -> dict[str, Any]:
    client = get_client()
    from services.dashboard_service import normalize_dashboard_days

    d = normalize_dashboard_days(days)
    since = datetime.now(UTC) - timedelta(days=d)
    since_iso = since.isoformat()

    event_rows: list[dict[str, Any]] = []
    try:
        er = (
            client.table("prospect_events")
            .select("event,timestamp,property_id,metadata")
            .gte("timestamp", since_iso)
            .limit(500)
            .execute()
        )
        event_rows = er.data or []
    except Exception:
        pass

    prop_names: dict[str, str] = {}
    try:
        pr = client.table("properties").select("id,name").limit(200).execute()
        for r in pr.data or []:
            prop_names[str(r["id"])] = str(r.get("name") or "Property")
    except Exception:
        pass

    event_ctr = Counter(str(e.get("event") or "unknown") for e in event_rows)
    top_obj = event_ctr.most_common(8)

    wins: list[dict[str, str]] = []
    for ev, n in top_obj[:5]:
        if "tour" in ev.lower() or "book" in ev.lower():
            wins.append({"lead": f"{ev}", "detail": f"{n} events in the last {d} days"})

    if not wins:
        wins = [{"lead": "Activity", "detail": f"{len(event_rows)} prospect events recorded in the last {d} days."}]

    blockers_items: list[dict[str, str]] = []
    try:
        bl = (
            client.table("property_onboarding_blockers")
            .select("message,severity")
            .eq("resolved", False)
            .limit(10)
            .execute()
        )
        for r in bl.data or []:
            blockers_items.append({"lead": str(r.get("message") or "Blocker"), "detail": str(r.get("severity") or "")})
    except Exception:
        pass
    if not blockers_items:
        blockers_items = [{"lead": "No open onboarding blockers", "detail": "n/a"}]

    objections_items = [{"topic": ev, "mentions": n} for ev, n in top_obj[:8]]

    def _humanize_event_code(ev: str) -> str:
        s = (ev or "").replace("_", " ").strip()
        return s[:1].upper() + s[1:] if s else ev

    next_actions = []
    for i, (ev, _) in enumerate(top_obj[:5], start=1):
        label = _humanize_event_code(str(ev))
        next_actions.append(
            {
                "n": i,
                "title": f'Prioritize follow-up for "{label}" activity',
                "subtitle": "Template fallback — enable OpenAI in .env for AI-written actions from your data.",
            }
        )

    today = datetime.now(UTC).date()
    iso_monday = today - timedelta(days=today.weekday())
    week_label = iso_monday.strftime("%b %d, %Y")

    summary_body = (
        f"In the last {d} days we recorded {len(event_rows)} prospect events across tracked properties. "
        f"Top signal: {top_obj[0][0] if top_obj else 'n/a'}."
    )

    return {
        "page": {"title": "Weekly Operator Brief", "weekLabelPrefix": "Week of"},
        "briefWeekLabel": week_label,
        "executiveSummary": {
            "title": "Executive Summary",
            "paragraphs": [{"body": summary_body}, {"body": "Review wins and blockers below; next actions prioritize the highest-volume event types."}],
        },
        "wins": {"title": "Biggest Wins", "items": wins},
        "blockers": {"title": "Biggest Blockers", "items": blockers_items},
        "objections": {"title": "Top Objections This Week", "items": objections_items},
        "nextActions": {"title": "Recommended Next Actions", "items": next_actions},
    }


def build_lesa_ai_weekly_brief(
    property_id: str | None = None, days: int = 7, *, use_llm: bool = True
) -> dict[str, Any]:
    """
    Lesa AI tab: compact DB digest (parallel fetch + feedback) → OpenAI → brief JSON.
    Falls back to rule-based `build_weekly_brief` if the model call fails.
    """
    from services.dashboard_service import collect_lesa_ai_digest_sync, normalize_dashboard_days
    from services.lesa_ai_llm import enrich_lesa_ai_page

    d = normalize_dashboard_days(days)
    fallback = build_weekly_brief(d)
    fb = fallback.setdefault("page", {})
    fb["title"] = "Weekly Operator Brief"
    fb["weekLabelPrefix"] = "Week of"
    digest = collect_lesa_ai_digest_sync(property_id, d)
    if isinstance(digest.get("week_range_label"), str) and digest["week_range_label"].strip():
        fallback["briefWeekLabel"] = digest["week_range_label"].strip()[:120]
    if not use_llm:
        return fallback
    return enrich_lesa_ai_page(digest, fallback)


def build_home_payload_from_parts(
    property_id: str | None,
    days: int,
    inv: dict[str, Any],
    leads: dict[str, Any],
) -> dict[str, Any]:
    from services.dashboard_service import normalize_dashboard_days

    d = normalize_dashboard_days(days)
    client = get_client()
    tpl = load_home_ui_copy(client)

    locale = tpl.get("locale") or {"dateLocale": "en-US", "headerTimeZone": "America/New_York"}
    tz_name = str(locale.get("headerTimeZone") or "America/New_York")
    try:
        now_local = datetime.now(ZoneInfo(tz_name))
        hour = now_local.hour
    except Exception:
        now_local = datetime.now(UTC)
        hour = now_local.hour

    greetings = tpl.get("greetings") or {}
    if hour < 12:
        header_greeting = str(greetings.get("morning") or "")
    elif hour < 17:
        header_greeting = str(greetings.get("afternoon") or "")
    else:
        header_greeting = str(greetings.get("evening") or "")

    hot_n = int(leads.get("hot") or 0)
    vac_n = len(inv.get("vacantUnits") or [])
    at_risk_n = sum(1 for x in inv.get("vacantUnits") or [] if x.get("status") == "atRisk")

    av_tpl = tpl.get("atRiskUnits") or {}
    vl_tmpl = str(av_tpl.get("vacantLabelTemplate") or "{days} days vacant")
    reason_fb = str(av_tpl.get("reasonFallback") or "")

    at_risk: list[dict[str, Any]] = []
    for i, u in enumerate(inv.get("vacantUnits") or []):
        if len(at_risk) >= 20:
            break
        if str(u.get("status")) == "atRisk" or int(u.get("days") or 0) >= 10:
            dv = int(u.get("days") or 0)
            at_risk.append(
                {
                    "id": f"risk-{u.get('id', i)}",
                    "unit": u.get("unitCode"),
                    "risk": "high" if u.get("status") == "atRisk" else "medium",
                    "vacantLabel": format_template(vl_tmpl, {"days": dv}),
                    "property": u.get("property"),
                    "reason": str(u.get("whyMatters") or reason_fb),
                }
            )

    fq_tpl = tpl.get("followUpQueue") or {}
    detail_fb = str(fq_tpl.get("detailFallback") or "")

    followup: list[dict[str, Any]] = []
    for i, row in enumerate((leads.get("data") or [])[:20]):
        heat = str(row.get("status") or "warm")
        followup.append(
            {
                "id": f"fu-{row.get('id')}",
                "name": row.get("name"),
                "property": row.get("property"),
                "detail": str(row.get("recommended_action") or detail_fb),
                "heat": "hot" if heat == "hot" else "warm",
                "timeAgo": _ago_from_iso(str(row.get("tour_time") or row.get("last_contact") or "")),
                "channel": "sms" if i % 2 == 0 else "email",
            }
        )

    lb_tpl = tpl.get("launchBlockers") or {}
    issue_def = str(lb_tpl.get("issueDefault") or "")
    detail_lb_fb = str(lb_tpl.get("detailFallback") or "")

    onb = build_onboarding_payload(property_id, d)
    launch_items: list[dict[str, Any]] = []
    for i, p in enumerate(onb.get("properties") or []):
        if str(p.get("status")) == "blocked" or (p.get("blockers") or []):
            b = p.get("blockers") or []
            launch_items.append(
                {
                    "id": f"lb-{p.get('id', i)}",
                    "name": p.get("name"),
                    "tag": "blocking",
                    "percent": int(p.get("completeness") or 40),
                    "issue": issue_def,
                    "detail": str(b[0]) if b else detail_lb_fb,
                }
            )
        if len(launch_items) >= 20:
            break

    ti_tpl = tpl.get("tourInsights") or {}
    tour_low_thr = int(ti_tpl.get("tourMentionsLowThreshold") or 3)

    since = datetime.now(UTC) - timedelta(days=d)
    prev_window_start = since - timedelta(days=d)
    tour_insights: list[dict[str, Any]] = []
    tour_total_events = 0
    prev_tour_total_events = 0
    try:
        er = (
            client.table("prospect_events")
            .select("event,property_id,timestamp")
            .gte("timestamp", since.isoformat())
            .limit(400)
            .execute()
        )
        by_prop: Counter[str] = Counter()
        for e in er.data or []:
            ev = str(e.get("event") or "").lower()
            if "tour" in ev:
                pid = str(e.get("property_id") or "")
                if pid:
                    by_prop[pid] += 1
        tour_total_events = int(sum(by_prop.values()))
        try:
            er_prev = (
                client.table("prospect_events")
                .select("event")
                .gte("timestamp", prev_window_start.isoformat())
                .lt("timestamp", since.isoformat())
                .limit(2000)
                .execute()
            )
            for row in er_prev.data or []:
                if "tour" in str(row.get("event") or "").lower():
                    prev_tour_total_events += 1
        except Exception:
            prev_tour_total_events = 0

        prop_names: dict[str, str] = {}
        if by_prop:
            ids = list(by_prop.keys())[:40]
            for batch in [ids[i : i + 12] for i in range(0, len(ids), 12)]:
                pr = client.table("properties").select("id,name").in_("id", batch).execute()
                for r in pr.data or []:
                    prop_names[str(r["id"])] = str(r.get("name") or "Property")
        for pid, mentions in by_prop.most_common(20):
            pname = prop_names.get(pid, "Property")
            if mentions >= tour_low_thr:
                row_text = (
                    f"Strong tour engagement at {pname}: {mentions} tour-related signals in the last {d} days."
                )
            else:
                row_text = (
                    f"Tour signals below typical for {pname} ({mentions} mentions in the last {d} days)."
                )
            tour_insights.append(
                {
                    "id": f"ti-{pid}",
                    "tone": "negative" if mentions < tour_low_thr else "positive",
                    "property": pname,
                    "text": row_text,
                    "mentions": mentions,
                }
            )
    except Exception:
        pass

    if prev_tour_total_events <= 0:
        trend_pct_display = "+100%" if tour_total_events > 0 else "0%"
    else:
        delta_pct = int(round((tour_total_events - prev_tour_total_events) / prev_tour_total_events * 100))
        trend_pct_display = f"{'+' if delta_pct >= 0 else ''}{delta_pct}%"

    ti_subtitle_tmpl = str(ti_tpl.get("subtitleTemplate") or "Last {d} days • {tour_total} tours analyzed")
    tour_insights_subtitle = format_template(
        ti_subtitle_tmpl,
        {"d": d, "tour_total": tour_total_events},
    )
    tour_trend_label = str(ti_tpl.get("trendLabel") or "Tour volume")

    fmt_ctx: dict[str, Any] = {
        "vac_n": vac_n,
        "hot_n": hot_n,
        "followup_n": len(followup),
        "at_risk_n": at_risk_n,
        "d": d,
    }

    pa_tpl = tpl.get("priorityActions") or {}
    priority_items: list[dict[str, Any]] = []
    for raw_pi in pa_tpl.get("items") or []:
        if not isinstance(raw_pi, dict):
            continue
        cta_path = str(raw_pi.get("ctaPath") or "").strip()
        if not cta_path:
            t = str(raw_pi.get("title") or "").lower()
            if "inventory" in t or "vacant" in t:
                cta_path = "/packages"
            elif "follow" in t or "pipeline" in t or "lead" in t:
                cta_path = "/users"
            elif "onboarding" in t or "blocker" in t or "launch" in t:
                cta_path = "/properties"
            else:
                cta_path = "/analytics"
        lines_in = raw_pi.get("lines") or []
        lines_out = [format_template(str(line), fmt_ctx) for line in lines_in if line is not None]
        priority_items.append(
            {
                "id": raw_pi.get("id"),
                "tag": raw_pi.get("tag") or "high",
                "icon": raw_pi.get("icon") or "Sparkles",
                "title": str(raw_pi.get("title") or ""),
                "ctaPath": cta_path,
                "lines": lines_out,
            }
        )

    dab = tpl.get("dailyAiBrief") or {}
    brief_paragraphs: list[dict[str, str]] = []
    for p in dab.get("fallbackParagraphs") or []:
        if isinstance(p, dict) and p.get("body"):
            row: dict[str, str] = {"body": format_template(str(p["body"]), fmt_ctx)}
            lead_raw = p.get("lead")
            if isinstance(lead_raw, str) and lead_raw.strip():
                row["lead"] = format_template(lead_raw.strip(), fmt_ctx)
            brief_paragraphs.append(row)
    if not brief_paragraphs:
        brief_paragraphs = [{"body": format_template("", fmt_ctx)}]
    # Home card: one short daily brief paragraph (merge template/DB multi-block; drop section leads).
    if len(brief_paragraphs) > 1:
        merged_bodies = [str(r.get("body") or "").strip() for r in brief_paragraphs if r.get("body")]
        brief_paragraphs = [{"body": " ".join(merged_bodies).strip()}] if merged_bodies else brief_paragraphs
    if brief_paragraphs:
        one = dict(brief_paragraphs[0])
        one.pop("lead", None)
        brief_paragraphs = [one]

    links = tpl.get("links") or {}
    full_brief_path = str(links.get("fullBriefPath") or "/ai")

    tour_rec_title = str(ti_tpl.get("recommendedActionTitle") or "")
    tour_rec_body = str(ti_tpl.get("recommendedActionBody") or "")

    low_tour_props = [str(x.get("property") or "") for x in tour_insights if x.get("tone") == "negative"][:4]
    high_tour_props = [str(x.get("property") or "") for x in tour_insights if x.get("tone") == "positive"][:4]
    at_risk_units_sample = [str(u.get("unit") or "") for u in at_risk[:6] if u.get("unit")]
    llm_metrics = {
        "window_days": d,
        "property_scope": property_id or "all_properties",
        "vacant_units_in_view": vac_n,
        "hot_leads": hot_n,
        "followup_queue_count": len(followup),
        "at_risk_marked_units": at_risk_n,
        "at_risk_panel_units": len(at_risk),
        "at_risk_unit_codes_sample": [x for x in at_risk_units_sample if x],
        "launch_blocker_properties": len(launch_items),
        "properties_with_tour_signals": len(tour_insights),
        "properties_low_tour_signal": sum(1 for x in tour_insights if x.get("tone") == "negative"),
        "tour_events_in_window": tour_total_events,
        "tour_volume_change_pct_label": trend_pct_display,
        "sample_low_tour_property_names": low_tour_props,
        "sample_strong_tour_property_names": high_tour_props,
    }
    brief_paragraphs, tour_rec_title, tour_rec_body = enrich_home_narrative_llm(
        property_id=property_id,
        window_days=d,
        metrics=llm_metrics,
        fallback_brief=brief_paragraphs,
        fallback_tour_title=tour_rec_title,
        fallback_tour_body=tour_rec_body,
    )

    labels = tpl.get("labels") or {}
    errors = tpl.get("errors") or {}

    return {
        "locale": locale,
        "headerGreeting": header_greeting,
        "headerSubtext": str(tpl.get("headerSubtext") or ""),
        "dailyAiBrief": {
            "title": str(dab.get("title") or ""),
            "subtitle": str(dab.get("subtitle") or ""),
            "paragraphs": brief_paragraphs,
            "fullBriefPath": full_brief_path,
            "fullBriefLinkLabel": str(dab.get("fullBriefLinkLabel") or ""),
        },
        "priorityActions": {
            "title": str(pa_tpl.get("title") or ""),
            "subtitle": str(pa_tpl.get("subtitle") or ""),
            "items": priority_items,
        },
        "atRiskUnits": {
            "title": str(av_tpl.get("title") or ""),
            "subtitle": str(av_tpl.get("subtitle") or ""),
            "summaryValue": str(len(at_risk)),
            "summaryLabel": str(av_tpl.get("summaryLabel") or ""),
            "items": at_risk,
            "ctaPath": str(av_tpl.get("ctaPath") or "/packages"),
            "ctaLabel": str(av_tpl.get("ctaLabel") or ""),
        },
        "launchBlockers": {
            "title": str(lb_tpl.get("title") or ""),
            "subtitle": str(lb_tpl.get("subtitle") or ""),
            "summaryValue": str(len(launch_items)),
            "summaryLabel": str(lb_tpl.get("summaryLabel") or ""),
            "items": launch_items,
            "ctaPath": str(lb_tpl.get("ctaPath") or "/properties"),
            "ctaLabel": str(lb_tpl.get("ctaLabel") or ""),
        },
        "followUpQueue": {
            "title": str(fq_tpl.get("title") or ""),
            "subtitle": str(fq_tpl.get("subtitle") or ""),
            "summaryValue": str(len(followup)),
            "summaryLabel": str(fq_tpl.get("summaryLabel") or ""),
            "items": followup,
            "ctaPath": str(fq_tpl.get("ctaPath") or "/users"),
            "ctaLabel": str(fq_tpl.get("ctaLabel") or ""),
        },
        "tourInsights": {
            "title": str(ti_tpl.get("title") or ""),
            "subtitle": tour_insights_subtitle,
            "trendValue": trend_pct_display,
            "trendLabel": tour_trend_label,
            "toursAnalyzedTotal": tour_total_events,
            "items": tour_insights,
            "recommendedActionTitle": tour_rec_title,
            "recommendedActionBody": tour_rec_body,
            "ctaPath": str(ti_tpl.get("ctaPath") or "/ai"),
            "ctaLabel": str(ti_tpl.get("ctaLabel") or ""),
        },
        "ui": {
            "labels": labels,
            "errors": errors,
        },
    }
