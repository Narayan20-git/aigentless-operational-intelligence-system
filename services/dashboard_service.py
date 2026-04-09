import asyncio
import random
from datetime import UTC, date, datetime, timedelta
from typing import Any

from config.database import get_client


def _select(table: str, fields: str = "*", limit: int = 100) -> list[dict[str, Any]]:
    res = get_client().table(table).select(fields).limit(limit).execute()
    return res.data or []


async def _aselect(table: str, fields: str = "*", limit: int = 100) -> list[dict[str, Any]]:
    return await asyncio.to_thread(_select, table, fields, limit)


def _iso_now_minus(hours: int) -> str:
    return (datetime.now(UTC) - timedelta(hours=hours)).isoformat()


async def get_home_payload() -> dict[str, Any]:
    properties, units, prospects = await asyncio.gather(
        _aselect("properties", "id,name,address", 30),
        _aselect("units", "id,unit,property_id", 40),
        _aselect("prospects", "id,first_name,last_name,created_at", 40),
    )

    property_name = {p["id"]: p.get("name", "Unknown Property") for p in properties}

    at_risk_units = []
    for i, u in enumerate(units[:20], start=1):
        at_risk_units.append(
            {
                "unit": u.get("unit") or f"U-{i:03d}",
                "risk": "high" if i % 3 == 0 else "medium",
                "vacantLabel": f"{5 + i} days vacant",
                "property": property_name.get(u.get("property_id"), "Unknown Property"),
                "reason": "Low inquiry velocity in the last 7 days",
            }
        )

    follow_up = []
    for i, p in enumerate(prospects[:20], start=1):
        name = f"{p.get('first_name') or 'Prospect'} {p.get('last_name') or i}".strip()
        follow_up.append(
            {
                "name": name,
                "property": properties[i % max(1, len(properties))].get("name", "Unknown Property")
                if properties
                else "Unknown Property",
                "detail": "Needs pricing clarification before applying",
                "heat": "hot" if i % 4 == 0 else ("warm" if i % 2 == 0 else "cold"),
                "timeAgo": f"{i}h ago",
                "channel": "sms" if i % 2 == 0 else "email",
            }
        )

    return {
        "locale": "en-US",
        "headerSubtext": "Portfolio pulse and action queue",
        "dailyAiBrief": {
            "title": "Daily AI Brief",
            "subtitle": "What changed since yesterday",
            "paragraphs": [
                "Lead quality improved across downtown properties.",
                "Two assets show rising vacancy pressure in 1BHK inventory.",
            ],
            "fullBriefPath": "/ai",
        },
        "priorityActions": {
            "items": [
                {
                    "id": "pa-1",
                    "tag": "high",
                    "icon": "alert",
                    "title": "Launch outreach campaign for stale units",
                    "lines": ["8 units are beyond 14 days vacant."],
                },
                {
                    "id": "pa-2",
                    "tag": "medium",
                    "icon": "sparkles",
                    "title": "Tighten pricing on high-tour low-app units",
                    "lines": ["Conversion gap persists in 2BHK segment."],
                },
            ]
        },
        "atRiskUnits": {"summaryValue": str(len(at_risk_units)), "items": at_risk_units},
        "launchBlockers": {
            "items": [
                {
                    "name": p.get("name", "Property"),
                    "tag": "blocker",
                    "percent": random.randint(35, 90),
                    "issue": "Onboarding checklist incomplete",
                    "detail": "Missing integration credential validation.",
                }
                for p in properties[:20]
            ]
        },
        "followUpQueue": {"items": follow_up},
        "tourInsights": {
            "items": [
                {
                    "tone": "neutral" if i % 3 else "negative",
                    "property": p.get("name", "Property"),
                    "text": "Prospects mention commute and parking most often.",
                    "mentions": i + 2,
                }
                for i, p in enumerate(properties[:20])
            ],
            "trend": "Objection volume stable week-over-week",
            "recommendedAction": "Emphasize transit and parking offers in AI scripts",
        },
    }


async def get_leads_summary_payload() -> dict[str, Any]:
    prospects, properties, units = await asyncio.gather(
        _aselect("prospects", "id,first_name,last_name,created_at,applied,leased", 100),
        _aselect("properties", "id,name", 40),
        _aselect("units", "id,unit,property_id", 80),
    )
    if not prospects:
        return {"total": 0, "hot": 0, "warm": 0, "cold": 0, "data": []}

    property_rows = properties or [{"id": None, "name": "Default Property"}]
    unit_rows = units or [{"unit": "U-001", "property_id": None}]
    cards = []
    hot = warm = cold = 0
    for i, p in enumerate(prospects[:30], start=1):
        status = "hot" if i % 3 == 0 else ("warm" if i % 3 == 1 else "cold")
        if status == "hot":
            hot += 1
        elif status == "warm":
            warm += 1
        else:
            cold += 1
        prop = property_rows[i % len(property_rows)]
        unit = unit_rows[i % len(unit_rows)]
        # Priority derives from DB state so the UI remains meaningful:
        # - Not applied / not leased => critical
        # - Applied / not leased => moderate
        # - Leased => low
        if not p.get("applied") and not p.get("leased"):
            priority = "critical"
        elif p.get("applied") and not p.get("leased"):
            priority = "moderate"
        else:
            priority = "low"

        cards.append(
            {
                "id": str(p["id"]),
                "name": f"{p.get('first_name') or 'Lead'} {p.get('last_name') or i}".strip(),
                "status": status,
                "priority": priority,
                "property": prop.get("name", "Unknown Property"),
                "unit": unit.get("unit", f"U-{i:03d}"),
                "tour_time": _iso_now_minus(48 - i),
                "last_contact": _iso_now_minus(i),
                "tags": ["New Lead"] if i % 2 == 0 else ["Returning"],
                "recommended_action": "Share limited-time offer and schedule a call",
                "objections": ["Budget", "Move-in timing"],
                "alternates": ["Unit with lower rent", "Flexible move-in date"],
                "ai_draft": "Hi! We have a matching option available this week.",
            }
        )
    return {"total": len(cards), "hot": hot, "warm": warm, "cold": cold, "data": cards}


async def get_inventory_payload() -> dict[str, Any]:
    units, properties, spaces = await asyncio.gather(
        _aselect("units", "id,unit,property_id,floorplan_id", 200),
        _aselect("properties", "id,name", 40),
        _aselect("spaces", "id,unit_id,availability_status,available_date", 200),
    )
    property_name = {p["id"]: p.get("name", "Property") for p in properties}
    space_by_unit = {s.get("unit_id"): s for s in spaces}

    vacant = []
    for i, u in enumerate(units[:40], start=1):
        s = space_by_unit.get(u.get("id"), {})
        status = "atRisk" if i % 4 == 0 else ("stale" if i % 5 == 0 else "healthy")
        days = 5 + i
        tours = i % 8
        apps = i % 4
        conv = f"{int((apps / max(1, tours)) * 100)}%" if tours else "0%"
        vacant.append(
            {
                "id": str(u["id"]),
                "unitCode": u.get("unit") or f"U-{i:03d}",
                "property": property_name.get(u.get("property_id"), "Unknown Property"),
                "unitType": "1BHK" if i % 2 == 0 else "2BHK",
                "status": status,
                "days": days,
                "tours": tours,
                "apps": apps,
                "conv": conv,
                "whyMatters": f"Availability status: {s.get('availability_status', 'vacant')}",
                "recommendedAction": "Run pricing + content refresh experiment for 7 days",
            }
        )

    table_units = vacant[:30]

    return {
        "page": {"title": "Inventory Intelligence", "description": "Vacancy and conversion health"},
        "metricCards": [
            {"id": "vacant", "value": str(len(table_units)), "label": "Vacant Units"},
            {"id": "atRisk", "value": str(sum(1 for v in table_units if v["status"] == "atRisk")), "label": "At Risk"},
            {"id": "stale", "value": str(sum(1 for v in table_units if v["status"] == "stale")), "label": "Stale"},
        ],
        "tableTitle": "Vacant Units",
        "emptyStateText": "No vacant inventory",
        "statusFilterLabels": {"all": "All", "atRisk": "At Risk", "stale": "Stale", "healthy": "Healthy"},
        "vacantUnits": table_units,
    }


async def get_property_onboarding_payload() -> dict[str, Any]:
    properties = await _aselect("properties", "id,name,created_at,go_live_date", 100)
    data = []
    today = date.today()
    for i, p in enumerate(properties[:30], start=1):
        go_live_raw = p.get("go_live_date")
        go_live: date | None = None
        if isinstance(go_live_raw, str):
            try:
                go_live = date.fromisoformat(go_live_raw[:10])
            except ValueError:
                go_live = None
        if go_live is None:
            go_live = today + timedelta(days=10)

        days_to_go_live = (go_live - today).days
        if days_to_go_live <= -7:
            status = "ready"
            completeness = 90 + (i % 11)
        elif days_to_go_live <= 14:
            status = "inProgress"
            completeness = 62 + (i % 26)
        else:
            status = "blocked"
            completeness = 35 + (i % 20)

        data.append(
            {
                "id": str(p["id"]),
                "name": p.get("name", f"Property {i}"),
                "status": status,
                "completeness": completeness,
                "alerts": []
                if status == "ready"
                else ["Missing CRM token", "Floorplan media pending"][: (2 if i % 2 else 1)],
                "lastUpdated": _iso_now_minus(i),
                "checklist": [
                    {"label": "Property profile", "percent": min(100, completeness + 10)},
                    {"label": "Inventory sync", "percent": max(20, completeness - 20)},
                    {"label": "Messaging setup", "percent": max(10, completeness - 30)},
                ],
                "blockers": [] if status != "blocked" else ["Awaiting legal checklist approval"],
            }
        )

    return {
        "page": {"title": "Property Onboarding", "description": "Activation progress and blockers"},
        "metricCards": [
            {"id": "ready", "value": str(sum(1 for p in data if p["status"] == "ready")), "label": "Ready"},
            {"id": "inProgress", "value": str(sum(1 for p in data if p["status"] == "inProgress")), "label": "In Progress"},
            {"id": "blocked", "value": str(sum(1 for p in data if p["status"] == "blocked")), "label": "Blocked"},
            {"id": "avg", "value": f"{int(sum(p['completeness'] for p in data) / max(1, len(data)))}%", "label": "Avg Completeness"},
        ],
        "listTitle": "Properties",
        "emptyStateText": "No properties available",
        "properties": data,
    }


async def get_portfolio_overview_payload() -> dict[str, Any]:
    properties = await _aselect("properties", "id,name,address", 60)
    cards = []
    for i, p in enumerate(properties[:30], start=1):
        cards.append(
            {
                "name": p.get("name", f"Property {i}"),
                "locationLine": "Urban District",
                "status": "healthy" if i % 4 else "watch",
                "health": 65 + (i % 30),
                "conversion": f"{12 + (i % 12)}%",
                "vacancy": str(6 + (i % 10)),
                "tours": str(20 + i),
                "insight": "Tour volume rising but app conversion lags.",
                "insightAlert": i % 5 == 0,
                "stressMetrics": [{"label": "Lead Volume", "value": "medium"}, {"label": "Tour-to-app", "value": "watch"}],
            }
        )

    return {
        "page": {"title": "Portfolio Overview", "description": "Portfolio-level KPIs"},
        "metricCards": [
            {"value": "92%", "label": "Occupancy", "footerKind": "positive", "footerText": "+1.2% WoW"},
            {"value": "18%", "label": "Tour to App", "footerKind": "neutral", "footerText": "Flat WoW"},
            {"value": "11d", "label": "Avg Vacancy Days", "footerKind": "negative", "footerText": "+0.9d WoW"},
        ],
        "portfolioProperties": cards,
        "recommendationsSectionTitle": "AI Recommendations",
        "recommendations": [
            {
                "icon": "sparkles",
                "title": f"Recommendation {i}",
                "description": "Adjust pricing and outreach cadence for underperforming segment.",
                "tags": ["leasing", "priority-high" if i % 3 == 0 else "priority-medium"],
                "action": "View details",
                "actionVariant": "primary",
            }
            for i in range(1, 21)
        ],
    }


async def get_weekly_brief_payload() -> dict[str, Any]:
    return {
        "page": {"title": "Weekly Operator Brief"},
        "briefWeekLabel": "Week of Apr 9, 2026",
        "executiveSummary": {
            "paragraphs": [
                "Portfolio traffic remained strong while conversion stabilized.",
                "Primary headwind is pricing sensitivity in high-vacancy clusters.",
            ]
        },
        "wins": {"items": [f"Win {i}: occupancy lift at selected assets" for i in range(1, 21)]},
        "blockers": {"items": [f"Blocker {i}: integration lag impacts sync windows" for i in range(1, 21)]},
        "objections": {"items": [{"topic": f"Objection Topic {i}", "mentions": 3 + i} for i in range(1, 21)]},
        "nextActions": {"items": [{"n": i, "title": f"Action {i}", "subtitle": "Owner: Ops team"} for i in range(1, 21)]},
    }


async def get_integrations_payload() -> dict[str, Any]:
    return {
        "summaryStrip": [
            {"label": "Connected", "display": "16"},
            {"label": "Needs Attention", "display": "4"},
            {"label": "Realtime Sync", "display": "10"},
        ],
        "page": {"title": "Integrations", "description": "Connection health across systems"},
        "filterOptions": ["All", "CRM", "PMS", "Comms", "Analytics"],
        "rateLimitBanner": {
            "title": "Rate-limit advisory",
            "description": "Some providers may delay refresh during peak windows.",
        },
        "integrations": [
            {
                "id": f"int-{i}",
                "name": f"Integration {i}",
                "category": ["CRM", "PMS", "Comms", "Analytics"][i % 4],
                "description": "Bi-directional sync for leasing workflows.",
                "connected": i % 5 != 0,
                "lastSync": _iso_now_minus(i),
                "syncRealtime": i % 3 != 0,
                "icon": "plug",
                "iconBg": "#F3F4F6",
                "iconColor": "#111827",
            }
            for i in range(1, 21)
        ],
    }


async def get_profile_payload() -> dict[str, Any]:
    return {
        "title": "Profile",
        "description": "User profile and preferences",
    }


async def get_header_payload() -> dict[str, Any]:
    return {
        "brand": {
            "name": "Aigentless",
            "logoSrc": "/logo.png",
            "homeAriaLabel": "Aigentless home",
        },
        "propertySelectorLabel": "All Properties",
        "dateRangeLabel": "Last 7 days",
        "search": {"placeholder": "Search...", "inputId": "global-search"},
    }


async def get_navigation_payload() -> dict[str, Any]:
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
