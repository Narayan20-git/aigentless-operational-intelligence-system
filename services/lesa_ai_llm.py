"""Lesa AI tab: OpenAI generates the weekly brief JSON from a compact DB digest (fast path)."""

from __future__ import annotations

import copy
import hashlib
import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

_LESA_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


def _lesa_cache_ttl_sec() -> float:
    raw = os.getenv("LESA_AI_CACHE_TTL_SEC", "").strip()
    if raw:
        try:
            return max(60.0, min(7200.0, float(raw)))
        except ValueError:
            pass
    return 600.0


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


def _openai_api_key() -> str:
    return os.getenv("OPENAI_API_KEY", "").strip()


def _openai_model() -> str:
    return os.getenv("OPENAI_MODEL", "").strip() or "gpt-4o-mini"


def _max_output_tokens() -> int:
    raw = os.getenv("LESA_AI_MAX_TOKENS", "").strip()
    if raw.isdigit():
        return max(800, min(4096, int(raw)))
    return 2200


def _request_timeout_sec() -> float:
    raw = os.getenv("LESA_AI_TIMEOUT_SEC", "").strip()
    if raw:
        try:
            return max(15.0, min(120.0, float(raw)))
        except ValueError:
            pass
    return 40.0


def _normalize_lesa_payload(llm: Any, fallback: dict[str, Any]) -> dict[str, Any]:
    """Merge model output onto fallback; coerce types the React page expects."""
    if not isinstance(llm, dict):
        return fallback
    out = copy.deepcopy(fallback)

    page = llm.get("page")
    if isinstance(page, dict):
        cur = out.setdefault("page", {})
        for k in ("title", "weekLabelPrefix"):
            v = page.get(k)
            if isinstance(v, str) and v.strip():
                cur[k] = v.strip()[:120]

    bl = llm.get("briefWeekLabel")
    if isinstance(bl, str) and bl.strip():
        out["briefWeekLabel"] = bl.strip()[:120]

    es = llm.get("executiveSummary")
    if isinstance(es, dict):
        block = out.setdefault("executiveSummary", {"title": "Executive Summary", "paragraphs": []})
        t = es.get("title")
        if isinstance(t, str) and t.strip():
            block["title"] = t.strip()[:120]
        paras = es.get("paragraphs")
        if isinstance(paras, list) and paras:
            norm: list[dict[str, str]] = []
            for p in paras[:6]:
                if not isinstance(p, dict):
                    continue
                body = p.get("body")
                if not isinstance(body, str) or not body.strip():
                    continue
                row: dict[str, str] = {"body": body.strip()[:1200]}
                lead = p.get("lead")
                if isinstance(lead, str) and lead.strip():
                    row["lead"] = lead.strip()[:240]
                norm.append(row)
            if norm:
                block["paragraphs"] = norm

    for key in ("wins", "blockers"):
        sec = llm.get(key)
        if not isinstance(sec, dict):
            continue
        block = out.setdefault(key, {"title": key.title(), "items": []})
        st = sec.get("title")
        if isinstance(st, str) and st.strip():
            block["title"] = st.strip()[:120]
        items = sec.get("items")
        if not isinstance(items, list):
            continue
        norm_items: list[dict[str, str]] = []
        for it in items[:12]:
            if isinstance(it, str) and it.strip():
                norm_items.append({"lead": it.strip()[:400], "detail": ""})
            elif isinstance(it, dict):
                lead = it.get("lead") or it.get("title") or ""
                detail = it.get("detail") or it.get("subtitle") or ""
                if isinstance(lead, str) and lead.strip():
                    norm_items.append(
                        {
                            "lead": lead.strip()[:400],
                            "detail": (detail.strip()[:600] if isinstance(detail, str) else ""),
                        }
                    )
        if norm_items:
            block["items"] = norm_items

    obj = llm.get("objections")
    if isinstance(obj, dict):
        block = out.setdefault("objections", {"title": "Top Objections", "items": []})
        ot = obj.get("title")
        if isinstance(ot, str) and ot.strip():
            block["title"] = ot.strip()[:120]
        oitems = obj.get("items")
        if isinstance(oitems, list) and oitems:
            norm_o: list[dict[str, Any]] = []
            for it in oitems[:12]:
                if not isinstance(it, dict):
                    continue
                topic = it.get("topic")
                if not isinstance(topic, str) or not topic.strip():
                    continue
                m = it.get("mentions")
                try:
                    mi = int(m) if m is not None else 0
                except (TypeError, ValueError):
                    mi = 0
                norm_o.append({"topic": topic.strip()[:200], "mentions": max(0, mi)})
            if norm_o:
                block["items"] = norm_o

    na = llm.get("nextActions")
    if isinstance(na, dict):
        block = out.setdefault("nextActions", {"title": "Next Actions", "items": []})
        nt = na.get("title")
        if isinstance(nt, str) and nt.strip():
            block["title"] = nt.strip()[:120]
        nitems = na.get("items")
        if isinstance(nitems, list) and nitems:
            norm_n: list[dict[str, Any]] = []
            for i, it in enumerate(nitems[:8], start=1):
                if not isinstance(it, dict):
                    continue
                title = it.get("title")
                sub = it.get("subtitle")
                if not isinstance(title, str) or not title.strip():
                    continue
                norm_n.append(
                    {
                        "n": int(it.get("n")) if isinstance(it.get("n"), int) else i,
                        "title": title.strip()[:240],
                        "subtitle": (sub.strip()[:500] if isinstance(sub, str) else ""),
                    }
                )
            if norm_n:
                for j, row in enumerate(norm_n, start=1):
                    row["n"] = j
                block["items"] = norm_n

    return out


_SYSTEM_PROMPT = """You output one JSON object for an operator-facing "Weekly Operator Brief" UI.

Hard rules:
- Use ONLY numbers, names, and themes present in database_digest. Never invent properties, units, people, or counts.
- Executive summary: 2–4 paragraphs; optional "lead" per paragraph for a bold first clause; weave occupancy estimate, tour/application signals, named properties from digest, and feedback themes when relevant.
- wins.title must be "Biggest Wins"; blockers.title "Biggest Blockers"; objections.title "Top Objections This Week"; nextActions.title "Recommended Next Actions"; page.title "Weekly Operator Brief".
- For objections.items: prefer feedback.objection_themes_from_feedback (topic + mentions). If that list is empty, derive topics from funnel_top_events with the same total event volume implied by digest.
- briefWeekLabel should match week_range_label in digest when provided.
- No markdown, no code fences in the JSON values.

Biggest Wins (wins.items) — same UI pattern as blockers: bold "lead" then em dash and gray "detail"; tone is positive and analytical:
- Produce 3–6 items. Each item MUST be {"lead": "...", "detail": "..."}.
- lead: A specific win using digest facts only — e.g. named property or unit from properties_named / unit_highlights; cite real conversion (conv_pct_text), tours, apps, days_vacant where it reflects strength (healthy status, strong conv); pipeline.bookings_in_window, pipeline.events_in_window, pipeline.hot; inventory.healthy_count, estimated_portfolio_occupancy_pct, avg_days_vacant_sample, avg_unit_conversion_pct, sum_tours_attributed / sum_applications_attributed when they support a positive story.
- detail: Short context after the dash — portfolio comparison using ONLY digest numbers (e.g. "highest conversion among highlighted units", "above portfolio avg X%", "N healthy vacant units in window") OR qualitative tie to funnel_top_events volume. Do not claim "last month", "QoQ", or prior-period deltas unless those numbers explicitly appear in database_digest (they usually do not — avoid invented trends).
- If positives are sparse, still surface the best available signals from digest (e.g. properties ready in onboarding, top funnel event counts, feedback.aggregate.top_likes themes with mention of ratings if present) without fabricating benchmarks.

Biggest Blockers (blockers.items) — operator-style bullets; UI shows bold "lead" then an em dash and gray "detail":
- Produce 3–6 items. Each item MUST be {"lead": "...", "detail": "..."}.
- lead: One tight headline (no trailing period) naming the problem. Pattern examples (use real digest names only): "[Property name] launch or onboarding stuck", "[Unit code] at [Property] vacant [N] days", "[Property] conversion risk". Pull property and unit strings only from properties_named, unit_highlights, or onboarding.properties_with_blockers.
- detail: One clause after the dash in the UI — the concrete why, grounded in digest: quote or paraphrase onboarding.open_blockers / properties_with_blockers.blocker_messages; OR tie unit_highlights (days_vacant, status, tours, apps, conv_pct_text) to a feedback theme from feedback.objection_themes_from_feedback or feedback.aggregate.top_improvements / comments; OR stale/at_risk counts from inventory. Use real day counts and mention counts from digest only.
- Do NOT output generic lines like "No open onboarding blockers" unless digest truly has zero blockers and zero at-risk/stale units — if data is thin, still phrase blockers from funnel or pipeline cold counts with accurate numbers.
- Do NOT invent missing photos, CRM gaps, or other asset issues unless the digest explicitly contains that signal (e.g. in blocker messages or feedback text).

Recommended Next Actions (nextActions.items) — generate like a senior PM brief, NOT generic funnel labels:
- Produce exactly 3–5 items. Each item: "n" (1..5), "title", "subtitle".
- title: One clear imperative for leasing ops. MUST name specific entities from database_digest only: property names from properties_named or unit_highlights, exact blocker text from onboarding.open_blockers or properties_with_blockers.blocker_messages, unit codes from unit_highlights, lead segments (e.g. "hot" prospects) using pipeline.hot / pipeline.warm and sample_leads.property when relevant.
- title MUST include a concrete time target using reference_calendar.today_date_iso / today_weekday_utc (e.g. "by Thursday", "by Tuesday noon", "before end of week") — pick a realistic day/time in the same calendar week as today_date_iso or the next few business days; never use a fake calendar.
- subtitle: One line explaining WHY this matters: launch/blocker risk, at-risk or stale unit from inventory, feedback.objection_themes_from_feedback theme to address on a named unit/property, or pipeline urgency. Quote counts and mentions only from digest (e.g. mentions from objection themes, pipeline.hot, at_risk_count).
- Do NOT write vague lines like "Review funnel step: X" or "Owner: Leasing ops". Do NOT invent dollar amounts, rent, or revenue; if no money figures exist in digest, describe impact qualitatively (e.g. "high conversion potential — N hot leads in window").
- Prioritize: (1) onboarding blockers blocking named properties, (2) at-risk/stale units with property+unit in unit_highlights, (3) top feedback objection themes tied to a property/unit when digest allows, (4) follow-up on hot/warm leads with count from pipeline."""


def enrich_lesa_ai_page(digest: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    """
    Ask OpenAI for the brief from a compact `digest` (from collect_lesa_ai_digest_sync).
    On missing key or errors, returns `fallback`.
    """
    if _truthy_env("SKIP_LESA_AI_LLM"):
        return fallback

    api_key = _openai_api_key()
    if not api_key:
        return fallback

    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("Lesa AI: openai package not installed")
        return fallback

    cache_key = hashlib.sha256(
        json.dumps(digest, sort_keys=True, default=str).encode()
    ).hexdigest()[:48]
    now = time.time()
    hit = _LESA_CACHE.get(cache_key)
    if hit and (now - hit[0]) <= _lesa_cache_ttl_sec():
        return hit[1]

    user_blob = json.dumps({"database_digest": digest}, ensure_ascii=True, separators=(",", ":"))
    client = OpenAI(api_key=api_key, timeout=_request_timeout_sec())
    model = _openai_model()

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.25,
            max_tokens=_max_output_tokens(),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": user_blob
                    + "\nReturn a single JSON object with keys: page, briefWeekLabel, executiveSummary, wins, blockers, objections, nextActions. "
                    "wins.items must use lead+detail pairs in the Biggest Wins style (positive headline + contextual detail from digest only). "
                    "blockers.items must use lead+detail pairs in the Biggest Blockers style (headline + evidence from digest). "
                    "nextActions.items must follow the Recommended Next Actions style in the system prompt (specific, dated titles; impact subtitles; no template funnel text).",
                },
            ],
        )
        text = (resp.choices[0].message.content or "").strip()
        parsed = json.loads(text) if text else {}
        merged = _normalize_lesa_payload(parsed, fallback)
        _LESA_CACHE[cache_key] = (now, merged)
        return merged
    except Exception as e:
        logger.warning("Lesa AI OpenAI skipped: %s", e)
        return fallback
