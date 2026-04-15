"""Optional Gemini enrichment for Home page narrative (daily brief + tour recommendation)."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)


def _daily_brief_as_single_paragraph(briefs: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    """Collapse multi-block / legacy briefs into one body for the home card."""
    if not briefs:
        return []
    parts: list[str] = []
    for p in briefs:
        if not isinstance(p, dict):
            continue
        b = str(p.get("body") or "").strip()
        if b:
            parts.append(b)
    if not parts:
        return []
    text = " ".join(parts)
    text = " ".join(text.split())[:1200]
    return [{"body": text.strip()}]

_HOME_LLM_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


def _home_llm_cache_ttl_sec() -> float:
    raw = os.getenv("HOME_LLM_CACHE_TTL_SEC", "").strip()
    if raw:
        try:
            return max(30.0, min(7200.0, float(raw)))
        except ValueError:
            pass
    return 300.0


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


def _gemini_api_key() -> str:
    return (os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip())


def enrich_home_narrative_llm(
    *,
    property_id: str | None,
    window_days: int,
    metrics: dict[str, Any],
    fallback_brief: list[dict[str, str]],
    fallback_tour_title: str,
    fallback_tour_body: str,
) -> tuple[list[dict[str, str]], str, str]:
    """
    Returns (brief_paragraphs, tour_recommended_title, tour_recommended_body).
    On any failure or missing key, returns fallbacks unchanged.
    """
    if _truthy_env("SKIP_HOME_LLM"):
        return fallback_brief, fallback_tour_title, fallback_tour_body
    api_key = _gemini_api_key()
    if not api_key:
        return fallback_brief, fallback_tour_title, fallback_tour_body

    cache_key = hashlib.sha256(
        json.dumps(
            {"p": property_id or "", "d": window_days, "m": metrics},
            sort_keys=True,
            default=str,
        ).encode()
    ).hexdigest()[:48]
    now = time.time()
    hit = _HOME_LLM_CACHE.get(cache_key)
    if hit and (now - hit[0]) <= _home_llm_cache_ttl_sec():
        data = hit[1]
        cached_brief = data.get("brief_paragraphs")
        norm_brief = _daily_brief_as_single_paragraph(cached_brief if isinstance(cached_brief, list) else None)
        return (
            norm_brief if norm_brief else fallback_brief,
            data.get("tour_title") or fallback_tour_title,
            data.get("tour_body") or fallback_tour_body,
        )

    prompt = {
        "task": (
            "Write an executive Daily AI Brief for multifamily leasing operators. "
            "This appears on the home dashboard as a summary; tone is confident and actionable, like a Lesa AI operator brief."
        ),
        "constraints": [
            "Use ONLY facts from metrics (counts, lists, labels). Do not invent property names beyond sample_* lists; if a list is empty, do not name specific properties.",
            "Return valid JSON with keys: brief_paragraphs, tour_recommended_title, tour_recommended_body.",
            "brief_paragraphs: array of EXACTLY ONE object: {\"body\": \"...\"}. No \"lead\" field. No section headers inside the text.",
            "That single body is the entire Daily Brief: one short, flowing paragraph (4-7 sentences, max ~950 characters). Write it as a tight executive summary for today—not a list, not labeled sections. Weave in: portfolio scale (vacant/hot/follow-up counts), at-risk inventory if relevant, pipeline urgency, and tour demand signals using the metrics; end with one crisp priority if space allows.",
            "tour_recommended_title: short heading, max 90 chars.",
            "tour_recommended_body: one paragraph, max 360 chars, aligned with tour metrics.",
            "No markdown, no bullet characters, no emoji, no ALL CAPS headings.",
        ],
        "metrics": metrics,
    }
    body = {
        "contents": [{"parts": [{"text": json.dumps(prompt, ensure_ascii=True)}]}],
        "generationConfig": {
            "temperature": 0.25,
            "topP": 0.9,
            "responseMimeType": "application/json",
        },
    }
    model = os.getenv("GEMINI_MODEL", "").strip() or "gemini-2.0-flash"
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=22) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        text = (
            raw.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        parsed = json.loads(text) if text else {}
        paras = parsed.get("brief_paragraphs")
        out_brief: list[dict[str, str]] = fallback_brief
        if isinstance(paras, list) and len(paras) >= 1:
            parts: list[str] = []
            for p in paras[:8]:
                if not isinstance(p, dict):
                    continue
                body = p.get("body")
                if isinstance(body, str) and body.strip():
                    parts.append(body.strip())
            if parts:
                # One daily brief paragraph (merge legacy multi-block responses into a single flow).
                combined = " ".join(parts)
                combined = " ".join(combined.split())[:1200]
                out_brief = [{"body": combined}]
        t_title = parsed.get("tour_recommended_title")
        t_body = parsed.get("tour_recommended_body")
        out_title = (
            str(t_title).strip()[:120] if isinstance(t_title, str) and t_title.strip() else fallback_tour_title
        )
        out_body = (
            str(t_body).strip()[:400] if isinstance(t_body, str) and t_body.strip() else fallback_tour_body
        )
        _HOME_LLM_CACHE[cache_key] = (
            now,
            {"brief_paragraphs": out_brief, "tour_title": out_title, "tour_body": out_body},
        )
        final_brief = _daily_brief_as_single_paragraph(out_brief) or fallback_brief
        return final_brief, out_title, out_body
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError, TypeError) as e:
        logger.warning("Home LLM enrichment skipped: %s", e)
        return fallback_brief, fallback_tour_title, fallback_tour_body
