"""Load Home dashboard copy from DB (dashboard_home_ui) with JSON file fallback."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DEFAULT_PATH = Path(__file__).resolve().parent / "data" / "home_ui_default.json"


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = dict(base)
    for k, v in overlay.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _load_json_file() -> dict[str, Any]:
    return json.loads(_DEFAULT_PATH.read_text(encoding="utf-8"))


def load_home_ui_copy(client: Any) -> dict[str, Any]:
    """Merge file defaults with optional `dashboard_home_ui.copy_json` row id=default."""
    raw = _load_json_file()
    try:
        r = client.table("dashboard_home_ui").select("copy_json").eq("id", "default").limit(1).execute()
        row = (r.data or [None])[0]
        cj = row.get("copy_json") if row else None
        if isinstance(cj, dict) and cj:
            raw = _deep_merge(raw, cj)
    except Exception:
        pass
    return raw


def format_template(s: str, ctx: dict[str, Any]) -> str:
    try:
        return s.format(**ctx)
    except (KeyError, ValueError):
        return s


def home_empty_shell_from_template(tpl: dict[str, Any]) -> dict[str, Any]:
    """Same shape as GET /dashboard/home for client merge when the home request fails."""
    dab = tpl.get("dailyAiBrief") or {}
    pa = tpl.get("priorityActions") or {}
    av = tpl.get("atRiskUnits") or {}
    lb = tpl.get("launchBlockers") or {}
    fq = tpl.get("followUpQueue") or {}
    ti = tpl.get("tourInsights") or {}
    links = tpl.get("links") or {}
    labels = tpl.get("labels") or {}
    errors = tpl.get("errors") or {}
    return {
        "locale": tpl.get("locale") or {},
        "headerGreeting": "",
        "headerSubtext": str(tpl.get("headerSubtext") or ""),
        "dailyAiBrief": {
            "title": str(dab.get("title") or ""),
            "subtitle": str(dab.get("subtitle") or ""),
            "paragraphs": [],
            "fullBriefPath": str(links.get("fullBriefPath") or "/ai"),
            "fullBriefLinkLabel": str(dab.get("fullBriefLinkLabel") or ""),
        },
        "priorityActions": {
            "title": str(pa.get("title") or ""),
            "subtitle": str(pa.get("subtitle") or ""),
            "items": [],
        },
        "atRiskUnits": {
            "title": str(av.get("title") or ""),
            "subtitle": str(av.get("subtitle") or ""),
            "summaryValue": "0",
            "summaryLabel": str(av.get("summaryLabel") or ""),
            "items": [],
            "ctaPath": str(av.get("ctaPath") or "/packages"),
            "ctaLabel": str(av.get("ctaLabel") or ""),
        },
        "launchBlockers": {
            "title": str(lb.get("title") or ""),
            "subtitle": str(lb.get("subtitle") or ""),
            "summaryValue": "0",
            "summaryLabel": str(lb.get("summaryLabel") or ""),
            "items": [],
            "ctaPath": str(lb.get("ctaPath") or "/properties"),
            "ctaLabel": str(lb.get("ctaLabel") or ""),
        },
        "followUpQueue": {
            "title": str(fq.get("title") or ""),
            "subtitle": str(fq.get("subtitle") or ""),
            "summaryValue": "0",
            "summaryLabel": str(fq.get("summaryLabel") or ""),
            "items": [],
            "ctaPath": str(fq.get("ctaPath") or "/users"),
            "ctaLabel": str(fq.get("ctaLabel") or ""),
        },
        "tourInsights": {
            "title": str(ti.get("title") or ""),
            "subtitle": format_template(
                str(ti.get("subtitleTemplate") or "Last {d} days • {tour_total} tours analyzed"),
                {"d": 7, "tour_total": 0},
            ),
            "trendValue": "0%",
            "trendLabel": str(ti.get("trendLabel") or "Tour volume"),
            "items": [],
            "recommendedActionTitle": str(ti.get("recommendedActionTitle") or ""),
            "recommendedActionBody": str(ti.get("recommendedActionBody") or ""),
            "ctaPath": str(ti.get("ctaPath") or "/ai"),
            "ctaLabel": str(ti.get("ctaLabel") or ""),
        },
        "ui": {"labels": labels, "errors": errors},
    }
