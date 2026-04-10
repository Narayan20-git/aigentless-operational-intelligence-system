import json
import os
from datetime import UTC, date, datetime, timedelta
from typing import Any

import psycopg
from dotenv import load_dotenv

load_dotenv()


def _db_url() -> str:
    db_url = (
        os.getenv("SUPABASE_DB_URL", "").strip()
        or os.getenv("DATABASE_URL", "").strip()
        or os.getenv("POSTGRES_URL", "").strip()
    )
    if not db_url:
        raise RuntimeError("Set SUPABASE_DB_URL (or DATABASE_URL/POSTGRES_URL) in .env")
    return db_url


def _iso_now_minus(hours: int) -> str:
    return (datetime.now(UTC) - timedelta(hours=hours)).isoformat()


def _fetch_rows(cur: psycopg.Cursor, table: str, fields: str, limit: int) -> list[dict[str, Any]]:
    cur.execute(f"select {fields} from {table} limit %s", (limit,))
    cols = [c.name for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _upsert(cur: psycopg.Cursor, key: str, payload: dict[str, Any]) -> None:
    cur.execute(
        """
        insert into public.ui_payloads (key, payload, updated_at)
        values (%s, %s::jsonb, now())
        on conflict (key) do update
        set payload = excluded.payload, updated_at = now()
        """,
        (key, json.dumps(payload)),
    )


def main() -> None:
    with psycopg.connect(_db_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                create table if not exists public.ui_payloads (
                  key text primary key,
                  payload jsonb not null,
                  updated_at timestamptz not null default now()
                )
                """
            )

            properties = _fetch_rows(cur, "public.properties", "id,name,go_live_date", 30)
            units = _fetch_rows(cur, "public.units", "id,unit,property_id", 80)
            prospects = _fetch_rows(cur, "public.prospects", "id,first_name,last_name,applied,leased", 60)

            property_name = {str(p["id"]): p.get("name") or "Property" for p in properties}
            prop_default = properties or [{"id": None, "name": "Property"}]
            unit_default = units or [{"id": None, "unit": "U-001", "property_id": None}]

            # home
            at_risk = []
            for i, u in enumerate(units[:20], start=1):
                at_risk.append(
                    {
                        "id": f"risk-{i}",
                        "unit": u.get("unit") or f"U-{i:03d}",
                        "risk": "high" if i % 3 == 0 else "medium",
                        "vacantLabel": f"{5 + i} days vacant",
                        "property": property_name.get(str(u.get("property_id")), "Property"),
                        "reason": "Low inquiry velocity in the last 7 days",
                    }
                )
            followup = []
            for i, p in enumerate(prospects[:20], start=1):
                followup.append(
                    {
                        "id": f"fu-{i}",
                        "name": f"{p.get('first_name') or 'Lead'} {p.get('last_name') or i}".strip(),
                        "property": prop_default[i % len(prop_default)].get("name", "Property"),
                        "detail": "Needs pricing clarification before applying",
                        "heat": "hot" if i % 4 == 0 else "warm",
                        "timeAgo": f"{i}h ago",
                        "channel": "sms" if i % 2 == 0 else "email",
                    }
                )
            _upsert(
                cur,
                "dashboard_home",
                {
                    "locale": {"dateLocale": "en-US", "headerTimeZone": "America/New_York"},
                    "headerSubtext": "Portfolio pulse and action queue",
                    "dailyAiBrief": {
                        "title": "Daily AI Brief",
                        "subtitle": "What changed since yesterday",
                        "paragraphs": [
                            {"body": "Lead quality improved across downtown properties."},
                            {"body": "Two assets show rising vacancy pressure in 1BHK inventory."},
                        ],
                        "fullBriefPath": "/ai",
                        "fullBriefLinkLabel": "Read full brief",
                    },
                    "priorityActions": {
                        "title": "Priority Actions",
                        "subtitle": "Top items to address today",
                        "items": [
                            {"id": "pa-1", "tag": "high", "icon": "AlertTriangle", "title": "Launch outreach campaign for stale units", "lines": ["8 units are beyond 14 days vacant."]},
                            {"id": "pa-2", "tag": "high", "icon": "Sparkles", "title": "Tighten pricing on high-tour low-app units", "lines": ["Conversion gap persists in 2BHK segment."]},
                        ],
                    },
                    "atRiskUnits": {"title": "At-Risk Units", "subtitle": "Units needing intervention", "summaryValue": str(len(at_risk)), "summaryLabel": "Units", "items": at_risk, "ctaPath": "/packages", "ctaLabel": "View all"},
                    "launchBlockers": {
                        "title": "Launch Blockers",
                        "subtitle": "Items delaying activation",
                        "summaryValue": str(min(20, len(properties))),
                        "summaryLabel": "Properties",
                        "items": [
                            {"id": f"lb-{i}", "name": p.get("name", "Property"), "tag": "blocking", "percent": 35 + (i % 55), "issue": "Onboarding checklist incomplete", "detail": "Missing integration credential validation."}
                            for i, p in enumerate(properties[:20], start=1)
                        ],
                        "ctaPath": "/properties",
                        "ctaLabel": "View all",
                    },
                    "followUpQueue": {"title": "Follow-Up Queue", "subtitle": "Leads requiring touchpoints", "summaryValue": str(len(followup)), "summaryLabel": "Leads", "items": followup, "ctaPath": "/users", "ctaLabel": "Open queue"},
                    "tourInsights": {
                        "title": "Tour Insights",
                        "subtitle": "Recent objection trends",
                        "trendValue": "Stable",
                        "trendLabel": "Week over week",
                        "items": [
                            {"id": f"ti-{i}", "tone": "negative" if i % 3 == 0 else "positive", "property": p.get("name", "Property"), "text": "Prospects mention commute and parking most often.", "mentions": 2 + i}
                            for i, p in enumerate(properties[:20], start=1)
                        ],
                        "recommendedActionTitle": "Recommended action",
                        "recommendedActionBody": "Emphasize transit and parking offers in AI scripts.",
                        "ctaPath": "/analytics",
                        "ctaLabel": "Open insights",
                    },
                },
            )

            # leads (optional snapshot only; GET /api/leads/summary uses live tables via dashboard_service)
            lead_rows = []
            hot = warm = cold = 0
            for i, p in enumerate(prospects[:30], start=1):
                status = "hot" if i % 3 == 0 else ("warm" if i % 3 == 1 else "cold")
                if status == "hot":
                    hot += 1
                elif status == "warm":
                    warm += 1
                else:
                    cold += 1
                if not p.get("applied") and not p.get("leased"):
                    priority = "critical"
                elif p.get("applied") and not p.get("leased"):
                    priority = "moderate"
                else:
                    priority = "low"
                prop = prop_default[i % len(prop_default)]
                unit = unit_default[i % len(unit_default)]
                lead_rows.append(
                    {
                        "id": str(p["id"]),
                        "name": f"{p.get('first_name') or 'Lead'} {p.get('last_name') or i}".strip(),
                        "status": status,
                        "priority": priority,
                        "property": prop.get("name", "Property"),
                        "unit": unit.get("unit", f"U-{i:03d}"),
                        "tour_time": _iso_now_minus(48 - i),
                        "last_contact": _iso_now_minus(i),
                        "tags": ["Returning"] if i % 2 else ["New Lead"],
                        "recommended_action": "Share limited-time offer and schedule a call",
                        "objections": ["Budget", "Move-in timing"],
                        "alternates": ["Unit with lower rent", "Flexible move-in date"],
                        "ai_draft": "Hi! We have a matching option available this week.",
                    }
                )
            _upsert(cur, "leads_summary", {"total": len(lead_rows), "hot": hot, "warm": warm, "cold": cold, "data": lead_rows})

            # inventory (optional snapshot only; GET /api/inventory/vacant-units uses live tables via dashboard_service)
            vacant_units = []
            for i, u in enumerate(units[:30], start=1):
                tours = i % 8
                apps = i % 4
                status = "atRisk" if i % 4 == 0 else ("stale" if i % 5 == 0 else "healthy")
                vacant_units.append(
                    {
                        "id": str(u["id"]),
                        "unitCode": u.get("unit") or f"A-{100+i}",
                        "property": property_name.get(str(u.get("property_id")), "Property"),
                        "unitType": "1BHK" if i % 2 == 0 else "2BHK",
                        "status": status,
                        "days": 5 + i,
                        "tours": tours,
                        "apps": apps,
                        "conv": f"{int((apps / max(1, tours)) * 100)}%" if tours else "0%",
                        "whyMatters": "Availability velocity is below benchmark.",
                        "recommendedAction": "Run pricing + content refresh experiment for 7 days",
                    }
                )
            _upsert(
                cur,
                "inventory_vacant_units",
                {
                    "page": {"title": "Inventory Intelligence", "description": "Vacancy and conversion health"},
                    "metricCards": [
                        {"id": "vacant", "value": str(len(vacant_units)), "label": "Vacant Units"},
                        {"id": "atRisk", "value": str(sum(1 for x in vacant_units if x["status"] == "atRisk")), "label": "At Risk"},
                        {"id": "stale", "value": str(sum(1 for x in vacant_units if x["status"] == "stale")), "label": "Stale"},
                    ],
                    "tableTitle": "Vacant Units",
                    "emptyStateText": "No vacant inventory",
                    "statusFilterLabels": {"all": "All", "atRisk": "At Risk", "stale": "Stale", "healthy": "Healthy"},
                    "vacantUnits": vacant_units,
                },
            )

            # properties onboarding
            onboarding_rows = []
            today = date.today()
            for i, p in enumerate(properties[:20], start=1):
                go_live = p.get("go_live_date")
                if isinstance(go_live, str):
                    try:
                        d = date.fromisoformat(go_live[:10])
                    except ValueError:
                        d = today + timedelta(days=10)
                else:
                    d = today + timedelta(days=10)
                diff = (d - today).days
                if diff <= -7:
                    status = "ready"
                    completeness = 90 + (i % 10)
                elif diff <= 14:
                    status = "inProgress"
                    completeness = 62 + (i % 25)
                else:
                    status = "blocked"
                    completeness = 35 + (i % 20)
                onboarding_rows.append(
                    {
                        "id": str(p["id"]),
                        "name": p.get("name", "Property"),
                        "status": status,
                        "completeness": completeness,
                        "alerts": [] if status == "ready" else ["Missing CRM token"] + (["Floorplan media pending"] if i % 2 else []),
                        "lastUpdated": _iso_now_minus(i),
                        "checklist": [
                            {"label": "Property profile", "percent": min(100, completeness + 10)},
                            {"label": "Inventory sync", "percent": max(20, completeness - 20)},
                            {"label": "Messaging setup", "percent": max(10, completeness - 30)},
                        ],
                        "blockers": [] if status != "blocked" else ["Awaiting legal checklist approval"],
                    }
                )
            _upsert(
                cur,
                "properties_onboarding",
                {
                    "page": {"title": "Property Onboarding", "description": "Activation progress and blockers"},
                    "metricCards": [
                        {"id": "ready", "value": str(sum(1 for p in onboarding_rows if p["status"] == "ready")), "label": "Ready"},
                        {"id": "inProgress", "value": str(sum(1 for p in onboarding_rows if p["status"] == "inProgress")), "label": "In Progress"},
                        {"id": "blocked", "value": str(sum(1 for p in onboarding_rows if p["status"] == "blocked")), "label": "Blocked"},
                        {"id": "avg", "value": f"{int(sum(p['completeness'] for p in onboarding_rows) / max(1, len(onboarding_rows)))}%", "label": "Avg Completeness"},
                    ],
                    "listTitle": "Properties",
                    "emptyStateText": "No properties available",
                    "properties": onboarding_rows,
                },
            )

            _upsert(
                cur,
                "portfolio_overview",
                {
                    "page": {"title": "Portfolio Overview", "description": "Portfolio-level KPIs"},
                    "metricCards": [
                        {"id": "m1", "value": "92%", "label": "Occupancy", "footerKind": "trend", "footerText": "+1.2% WoW"},
                        {"id": "m2", "value": "18%", "label": "Tour to App", "footerKind": "plain", "footerText": "Flat WoW"},
                        {"id": "m3", "value": "11d", "label": "Avg Vacancy Days", "footerKind": "plain", "footerText": "+0.9d WoW"},
                    ],
                    "portfolioProperties": [
                        {
                            "id": str(p["id"]),
                            "name": p.get("name", "Property"),
                            "locationLine": "Urban District",
                            "status": "healthy" if (i % 4) else "watch",
                            "health": 65 + (i % 30),
                            "conversion": f"{12 + (i % 12)}",
                            "vacancy": str(6 + (i % 10)),
                            "tours": str(20 + i),
                            "insight": "Tour volume rising but app conversion lags.",
                            "insightAlert": i % 5 == 0,
                            "stressMetrics": [{"label": "Lead Volume", "value": "medium"}],
                        }
                        for i, p in enumerate(properties[:20], start=1)
                    ],
                    "recommendationsSectionTitle": "AI Recommendations",
                    "recommendations": [
                        {
                            "id": f"rec-{i}",
                            "icon": "chart",
                            "title": f"Recommendation {i}",
                            "description": "Adjust pricing and outreach cadence for underperforming segments.",
                            "tags": [{"label": "leasing", "tone": "gray"}, {"label": "priority", "tone": "yellow"}],
                            "action": "View details",
                            "actionVariant": "solid",
                        }
                        for i in range(1, 21)
                    ],
                },
            )

            _upsert(
                cur,
                "briefs_weekly",
                {
                    "page": {"title": "Weekly Operator Brief"},
                    "briefWeekLabel": "Week of Apr 9, 2026",
                    "executiveSummary": {"title": "Executive Summary", "paragraphs": [{"body": "Portfolio traffic remained strong while conversion stabilized."}]},
                    "wins": {"title": "Wins", "items": [f"Win {i}: occupancy lift at selected assets" for i in range(1, 21)]},
                    "blockers": {"title": "Blockers", "items": [f"Blocker {i}: integration lag impacts sync windows" for i in range(1, 21)]},
                    "objections": {"title": "Top Objections", "items": [{"topic": f"Objection Topic {i}", "mentions": 3 + i} for i in range(1, 21)]},
                    "nextActions": {"title": "Next Actions", "items": [{"n": i, "title": f"Action {i}", "subtitle": "Owner: Ops team"} for i in range(1, 21)]},
                },
            )

            _upsert(
                cur,
                "integrations",
                {
                    "summaryStrip": [{"label": "Connected", "display": "16"}, {"label": "Needs Attention", "display": "4"}, {"label": "Realtime Sync", "display": "10"}],
                    "page": {"title": "Integrations", "description": "Connection health across systems"},
                    "filterOptions": ["All", "CRM", "PMS", "Comms", "Analytics"],
                    "rateLimitBanner": {"emphasis": "Rate-limit advisory.", "text": "Some providers may delay refresh during peak windows.", "configureLabel": "Configure"},
                    "integrations": [
                        {
                            "id": f"int-{i}",
                            "name": f"Integration {i}",
                            "category": ["CRM", "PMS", "Comms", "Analytics"][i % 4],
                            "description": "Bi-directional sync for leasing workflows.",
                            "connected": i % 5 != 0,
                            "lastSync": _iso_now_minus(i),
                            "syncRealtime": i % 3 != 0,
                            "icon": "Plug",
                            "iconBg": "bg-gray-100",
                            "iconColor": "text-gray-800",
                        }
                        for i in range(1, 21)
                    ],
                },
            )

            _upsert(cur, "profile_summary", {"title": "Profile", "description": "User profile and preferences"})
            _upsert(
                cur,
                "ui_header",
                {
                    "brand": {"name": "Aigentless", "logoSrc": "/logo.png", "homeAriaLabel": "Aigentless home"},
                    "propertySelectorLabel": "All Properties",
                    "dateRangeLabel": "Last 7 days",
                    "search": {"placeholder": "Search...", "inputId": "global-search"},
                },
            )
            _upsert(
                cur,
                "ui_navigation",
                {
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
                },
            )

    print("ui_payloads synced successfully.")


if __name__ == "__main__":
    main()

