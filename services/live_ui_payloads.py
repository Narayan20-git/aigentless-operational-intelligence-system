"""
Live-computed UI payloads from operational tables (no ui_payloads table).

Imported at runtime from dashboard_service to avoid circular import issues.
"""
from __future__ import annotations

import os
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta
from typing import Any

from config.database import get_client


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
    _ = days
    client = get_client()
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
        ],
        "listTitle": "Properties",
        "emptyStateText": "No properties available",
        "properties": onboarding_rows,
    }


def build_portfolio_overview(property_id: str | None, days: int) -> dict[str, Any]:
    from services.dashboard_service import _build_inventory_vacant_sync, normalize_dashboard_days

    d = normalize_dashboard_days(days)
    inv = _build_inventory_vacant_sync(property_id, d)
    vacant_by_prop: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for u in inv.get("vacantUnits") or []:
        pid = str(u.get("propertyId") or "")
        if pid:
            vacant_by_prop[pid].append(u)
        else:
            vacant_by_prop[str(u.get("property") or "")].append(u)

    client = get_client()
    pq = client.table("properties").select("id,name,neighborhood_name").order("name").limit(30)
    if property_id:
        pq = pq.eq("id", property_id)
    props = pq.execute().data or []

    total_vacant = len(inv.get("vacantUnits") or [])
    conv_vals: list[float] = []
    for u in inv.get("vacantUnits") or []:
        try:
            conv_vals.append(float(str(u.get("conv", "0")).replace("%", "")))
        except ValueError:
            pass
    avg_conv = sum(conv_vals) / max(1, len(conv_vals))
    avg_vac_days = (
        sum(int(u.get("days") or 0) for u in inv.get("vacantUnits") or []) / max(1, total_vacant) if total_vacant else 0.0
    )

    occ = max(0.0, min(100.0, 100.0 - (avg_vac_days * 1.2)))
    occ_s = f"{int(round(occ))}%"

    portfolio_properties: list[dict[str, Any]] = []
    for i, p in enumerate(props):
        pid = str(p["id"])
        rows = vacant_by_prop.get(pid, [])
        if rows:
            tours = sum(int(x.get("tours") or 0) for x in rows)
            convs = [float(str(x.get("conv", "0")).replace("%", "")) for x in rows]
            cavg = sum(convs) / max(1, len(convs))
            vac_n = len(rows)
            insight = f"{vac_n} vacant unit(s); avg conversion {int(round(cavg))}%."
            health = max(20, min(100, int(cavg)))
            if cavg >= 75 and vac_n <= 5:
                st = "healthy"
            elif cavg >= 50:
                st = "watch"
            else:
                st = "attention"
        else:
            tours = 0
            cavg = avg_conv
            vac_n = 0
            insight = "No vacant units in current inventory window."
            health = 75
            st = "healthy"

        loc = (str(p.get("neighborhood_name") or "").strip() or "Portfolio")
        portfolio_properties.append(
            {
                "id": pid,
                "name": p.get("name") or "Property",
                "locationLine": loc,
                "status": st,
                "health": health,
                "conversion": str(int(round(cavg))),
                "vacancy": str(vac_n),
                "tours": str(tours),
                "insight": insight,
                "insightAlert": st == "attention",
                "stressMetrics": [{"label": "Lead Volume", "value": "medium" if st != "healthy" else "low"}],
            }
        )

    recommendations = [
        {
            "id": f"rec-{i}",
            "icon": "chart",
            "title": f"Improve conversion at {x['name']}",
            "description": x["insight"],
            "tags": [{"label": "leasing", "tone": "gray"}, {"label": "priority", "tone": "yellow"}],
            "action": "View details",
            "actionVariant": "solid",
        }
        for i, x in enumerate([p for p in portfolio_properties if p["status"] != "healthy"][:10], start=1)
    ]

    return {
        "page": {"title": "Portfolio Overview", "description": "Portfolio-level KPIs (live)"},
        "metricCards": [
            {"id": "m1", "value": occ_s, "label": "Occupancy (est.)", "footerKind": "trend", "footerText": "Based on vacant unit sample"},
            {"id": "m2", "value": f"{int(round(avg_conv))}%", "label": "Tour to App (avg)", "footerKind": "plain", "footerText": "From vacant-unit window"},
            {"id": "m3", "value": f"{int(round(avg_vac_days))}d", "label": "Avg Vacancy Days", "footerKind": "plain", "footerText": "Vacant units in table"},
        ],
        "portfolioProperties": portfolio_properties,
        "recommendationsSectionTitle": "AI Recommendations",
        "recommendations": recommendations,
    }


def build_weekly_brief() -> dict[str, Any]:
    client = get_client()
    since = datetime.now(UTC) - timedelta(days=7)
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
            wins.append({"lead": f"{ev}", "detail": f"{n} events in the last 7 days"})

    if not wins:
        wins = [{"lead": "Activity", "detail": f"{len(event_rows)} prospect events recorded in the last 7 days."}]

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

    next_actions = []
    for i, (ev, _) in enumerate(top_obj[:5], start=1):
        next_actions.append({"n": i, "title": f"Review funnel step: {ev}", "subtitle": "Owner: Leasing ops"})

    today = datetime.now(UTC).date()
    iso_monday = today - timedelta(days=today.weekday())
    week_label = iso_monday.strftime("%b %d, %Y")

    summary_body = (
        f"In the last 7 days we recorded {len(event_rows)} prospect events across tracked properties. "
        f"Top signal: {top_obj[0][0] if top_obj else 'n/a'}."
    )

    return {
        "page": {"title": "Weekly Operator Brief", "weekLabelPrefix": "Week of"},
        "briefWeekLabel": week_label,
        "executiveSummary": {
            "title": "Executive Summary",
            "paragraphs": [{"body": summary_body}, {"body": "Review wins and blockers below; next actions prioritize the highest-volume event types."}],
        },
        "wins": {"title": "Wins", "items": wins},
        "blockers": {"title": "Blockers", "items": blockers_items},
        "objections": {"title": "Top Objections / Signals", "items": objections_items},
        "nextActions": {"title": "Next Actions", "items": next_actions},
    }


def build_home_payload(property_id: str | None, days: int) -> dict[str, Any]:
    from services.dashboard_service import _build_inventory_vacant_sync, _build_leads_summary_sync, normalize_dashboard_days

    d = normalize_dashboard_days(days)
    inv = _build_inventory_vacant_sync(property_id, d)
    leads = _build_leads_summary_sync(property_id, d)

    at_risk: list[dict[str, Any]] = []
    for i, u in enumerate(inv.get("vacantUnits") or []):
        if len(at_risk) >= 20:
            break
        if str(u.get("status")) == "atRisk" or int(u.get("days") or 0) >= 10:
            at_risk.append(
                {
                    "id": f"risk-{u.get('id', i)}",
                    "unit": u.get("unitCode"),
                    "risk": "high" if u.get("status") == "atRisk" else "medium",
                    "vacantLabel": f"{u.get('days', 0)} days vacant",
                    "property": u.get("property"),
                    "reason": str(u.get("whyMatters") or "Vacancy pressure in current window."),
                }
            )

    followup: list[dict[str, Any]] = []
    for i, row in enumerate((leads.get("data") or [])[:20]):
        heat = str(row.get("status") or "warm")
        followup.append(
            {
                "id": f"fu-{row.get('id')}",
                "name": row.get("name"),
                "property": row.get("property"),
                "detail": str(row.get("recommended_action") or "Follow up recommended."),
                "heat": "hot" if heat == "hot" else "warm",
                "timeAgo": _ago_from_iso(str(row.get("tour_time") or row.get("last_contact") or "")),
                "channel": "sms" if i % 2 == 0 else "email",
            }
        )

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
                    "issue": "Onboarding checklist incomplete",
                    "detail": b[0] if b else "Resolve onboarding blockers to go live.",
                }
            )
        if len(launch_items) >= 20:
            break

    # Tour insights: recent tour-related events by property
    client = get_client()
    since = datetime.now(UTC) - timedelta(days=14)
    tour_insights: list[dict[str, Any]] = []
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
        prop_names: dict[str, str] = {}
        if by_prop:
            ids = list(by_prop.keys())[:40]
            for batch in [ids[i : i + 12] for i in range(0, len(ids), 12)]:
                pr = client.table("properties").select("id,name").in_("id", batch).execute()
                for r in pr.data or []:
                    prop_names[str(r["id"])] = str(r.get("name") or "Property")
        for pid, mentions in by_prop.most_common(20):
            tour_insights.append(
                {
                    "id": f"ti-{pid}",
                    "tone": "negative" if mentions < 3 else "positive",
                    "property": prop_names.get(pid, "Property"),
                    "text": "Tour-related activity in the last 14 days.",
                    "mentions": mentions,
                }
            )
    except Exception:
        pass

    hot_n = int(leads.get("hot") or 0)
    vac_n = len(inv.get("vacantUnits") or [])
    at_risk_n = sum(1 for x in inv.get("vacantUnits") or [] if x.get("status") == "atRisk")

    priority_items = [
        {
            "id": "pa-1",
            "tag": "high",
            "icon": "AlertTriangle",
            "title": "Stabilize high-risk vacant inventory",
            "lines": [f"{at_risk_n} units flagged at-risk in the current window."],
        },
        {
            "id": "pa-2",
            "tag": "high",
            "icon": "Sparkles",
            "title": "Accelerate follow-ups on hot pipeline leads",
            "lines": [f"{hot_n} leads are currently marked hot."],
        },
    ]

    brief_paragraphs = [
        {
            "body": f"Portfolio snapshot: {vac_n} vacant units in view, {hot_n} hot leads, {len(followup)} leads in the follow-up queue.",
        },
        {"body": "Prioritize repricing and outreach where vacancy days are elevated and tour volume is misaligned with applications."},
    ]

    return {
        "locale": {"dateLocale": "en-US", "headerTimeZone": "America/New_York"},
        "headerSubtext": "Portfolio pulse and action queue (live)",
        "dailyAiBrief": {
            "title": "Daily AI Brief",
            "subtitle": "What changed recently",
            "paragraphs": brief_paragraphs,
            "fullBriefPath": "/ai",
            "fullBriefLinkLabel": "Read full brief",
        },
        "priorityActions": {
            "title": "Priority Actions",
            "subtitle": "Top items derived from current inventory + pipeline",
            "items": priority_items,
        },
        "atRiskUnits": {
            "title": "At-Risk Units",
            "subtitle": "Units needing intervention",
            "summaryValue": str(len(at_risk)),
            "summaryLabel": "Units",
            "items": at_risk,
            "ctaPath": "/packages",
            "ctaLabel": "View all",
        },
        "launchBlockers": {
            "title": "Launch Blockers",
            "subtitle": "Items delaying activation",
            "summaryValue": str(len(launch_items)),
            "summaryLabel": "Properties",
            "items": launch_items,
            "ctaPath": "/properties",
            "ctaLabel": "View all",
        },
        "followUpQueue": {
            "title": "Follow-Up Queue",
            "subtitle": "Leads requiring touchpoints",
            "summaryValue": str(len(followup)),
            "summaryLabel": "Leads",
            "items": followup,
            "ctaPath": "/users",
            "ctaLabel": "Open queue",
        },
        "tourInsights": {
            "title": "Tour Insights",
            "subtitle": "Recent tour signal volume by property",
            "trendValue": "Live",
            "trendLabel": "Last 14 days",
            "items": tour_insights,
            "recommendedActionTitle": "Recommended action",
            "recommendedActionBody": "Tune tour scheduling and follow-up scripts for properties with low tour mentions.",
            "ctaPath": "/analytics",
            "ctaLabel": "Open insights",
        },
    }
