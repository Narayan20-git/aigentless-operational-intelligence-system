"""Batch OpenAI enrichment for Lead Prioritization: guest tour feedback, alternates, and personalized drafts."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from config.database import get_client

logger = logging.getLogger(__name__)

_LEAD_CARD_CACHE: dict[str, tuple[float, dict[str, dict[str, Any]]]] = {}
_MAX_LEADS_PER_LLM_CALL = 22
_CHUNK = 40


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


def _lead_card_cache_ttl_sec() -> float:
    raw = os.getenv("LEAD_CARD_LLM_CACHE_TTL_SEC", "").strip()
    if raw:
        try:
            return max(30.0, min(7200.0, float(raw)))
        except ValueError:
            pass
    return 300.0


def _lead_card_openai_timeout_sec() -> float:
    raw = os.getenv("LEAD_CARD_LLM_TIMEOUT_SEC", "").strip()
    if raw:
        try:
            return max(12.0, min(120.0, float(raw)))
        except ValueError:
            pass
    return 45.0


def _lead_card_max_tokens_for_batch(n_leads: int) -> int:
    cap = int(os.getenv("LEAD_CARD_LLM_MAX_TOKENS", "3200") or 3200)
    cap = max(900, min(5000, cap))
    est = 650 + 185 * max(1, n_leads)
    return min(cap, est)


def heuristic_lead_cards_only(lead_rows: list[dict[str, Any]]) -> None:
    """Fill recommended_action / objections / alternates / ai_draft without OpenAI; strip internal keys."""
    if not lead_rows:
        return
    for r in lead_rows:
        _apply_heuristic_fallback([r])
    _strip_internal_lead_fields(lead_rows)


def _chunks(seq: list[str], size: int = _CHUNK) -> list[list[str]]:
    return [seq[i : i + size] for i in range(0, len(seq), size)]


def _openai_key() -> str:
    return os.getenv("OPENAI_API_KEY", "").strip()


def _openai_model() -> str:
    return os.getenv("OPENAI_MODEL", "").strip() or "gpt-4o-mini"


def _feedback_rows_for_prospects(client: Any, prospect_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
    """Tour feedback for this guest: feedback.profile_id = prospect id, and feedback.booking_id on their tours."""
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if not prospect_ids:
        return {}
    uniq = list(dict.fromkeys(prospect_ids))
    per_cap = 8

    booking_to_prospect: dict[str, str] = {}
    for batch in _chunks(uniq):
        try:
            br = (
                client.table("bookings")
                .select("id,profile_id")
                .in_("profile_id", batch)
                .order("start_time", desc=True)
                .limit(400)
                .execute()
            )
            for row in br.data or []:
                bid = str(row.get("id") or "")
                pid = str(row.get("profile_id") or "")
                if bid and pid:
                    booking_to_prospect[bid] = pid
        except Exception:
            pass

    seen_keys: set[tuple[Any, ...]] = set()

    def _append(pid: str, row: dict[str, Any]) -> None:
        if len(out[pid]) >= per_cap:
            return
        key = (pid, row.get("id"), str(row.get("created_at") or ""), str(row.get("booking_id") or ""))
        if key in seen_keys:
            return
        seen_keys.add(key)
        out[pid].append(row)

    for batch in _chunks(uniq):
        try:
            r = (
                client.table("feedback")
                .select("id,profile_id,floorplan_id,raw_feedback,type,booking_id,created_at")
                .in_("profile_id", batch)
                .order("created_at", desc=True)
                .limit(800)
                .execute()
            )
            for row in r.data or []:
                pid = str(row.get("profile_id") or "")
                if pid:
                    _append(pid, row)
        except Exception:
            pass

    all_bids = list(dict.fromkeys(booking_to_prospect.keys()))
    for i in range(0, len(all_bids), _CHUNK):
        chunk = all_bids[i : i + _CHUNK]
        try:
            r = (
                client.table("feedback")
                .select("id,profile_id,floorplan_id,raw_feedback,type,booking_id,created_at")
                .in_("booking_id", chunk)
                .order("created_at", desc=True)
                .limit(400)
                .execute()
            )
            for row in r.data or []:
                bid = str(row.get("booking_id") or "")
                pid = str(row.get("profile_id") or "") or booking_to_prospect.get(bid, "")
                if pid:
                    _append(pid, row)
        except Exception:
            pass

    return dict(out)


def _summarize_guest_tour_feedback(rows: list[dict[str, Any]]) -> dict[str, Any]:
    likes: list[str] = []
    improvements: list[str] = []
    free_text: list[str] = []
    ratings: list[str] = []
    types: list[str] = []
    for r in rows:
        t = str(r.get("type") or "").strip()
        if t:
            types.append(t)
        raw = r.get("raw_feedback")
        if isinstance(raw, str) and raw.strip():
            free_text.append(raw.strip()[:220])
            continue
        if not isinstance(raw, dict):
            continue
        rating = str(raw.get("rating") or raw.get("notes") or "").strip()
        if rating and len(rating) < 80:
            ratings.append(rating[:80])
        notes = raw.get("notes")
        if notes and str(notes).strip():
            free_text.append(str(notes).strip()[:220])
        for x in raw.get("likes") or []:
            s = str(x or "").strip()[:120]
            if s and s not in likes:
                likes.append(s)
        for x in raw.get("improvements") or []:
            s = str(x or "").strip()[:120]
            if s and s not in improvements:
                improvements.append(s)
        for key in ("additionalCommentsLikes", "additionalCommentsImprovements", "dislikes"):
            c = str(raw.get(key) or "").strip()
            if len(c) > 8:
                free_text.append(c[:220])
    return {
        "submission_count": len(rows),
        "feedback_row_types": list(dict.fromkeys(types))[:6],
        "likes": likes[:12],
        "improvements_or_concerns": improvements[:12],
        "free_text_snippets": free_text[:6],
        "rating_or_note_tokens": ratings[:6],
    }


def _scoped_feedback_rows_for_tour(
    rows: list[dict[str, Any]],
    tour_booking_ids: list[str],
    tour_floorplan_ids: list[str],
) -> list[dict[str, Any]]:
    """Prefer feedback rows tied to this tour (booking and/or floorplan of the unit toured)."""
    if not rows:
        return []
    tb = {str(x) for x in tour_booking_ids if x}
    tf = {str(x) for x in tour_floorplan_ids if x}
    if not tb and not tf:
        return list(rows)[:10]
    scoped: list[dict[str, Any]] = []
    for row in rows:
        bid = str(row.get("booking_id") or "")
        fp = str(row.get("floorplan_id") or "")
        if bid and bid in tb:
            scoped.append(row)
        elif fp and fp in tf:
            scoped.append(row)
    if scoped:
        return scoped[:10]
    return list(rows)[:10]


# Representative tour concerns when DB has no (or thin) feedback for this guest/tour.
_DUMMY_CONCERN_SETS: list[list[str]] = [
    ["Limited natural light in main living area", "Storage and closet space"],
    ["Bathroom size and layout", "Noise from common areas or neighbors"],
    ["Kitchen counter and cabinet space", "In-unit laundry vs hookups"],
    ["Pet policy and monthly pet rent", "Lease start date flexibility"],
    ["Parking or garage availability", "Balcony / outdoor space"],
    ["Price compared with similar nearby communities", "Move-in special or concessions"],
    ["Floorplan flow and bedroom separation", "HVAC and temperature comfort"],
    ["Package delivery and building access", "Guest parking"],
]


def _augment_objections_from_dummy_if_sparse(summary: dict[str, Any], lead: dict[str, Any]) -> None:
    """Ensure 2–3 concrete 'tour objection' lines for the LLM; fill gaps with deterministic demo themes."""
    imp = list(summary.get("improvements_or_concerns") or [])
    db_n = int(summary.get("submission_count", 0) or 0)
    target = 3 if db_n == 0 else 2
    if len(imp) >= target:
        summary["includes_synthetic_tour_concerns"] = False
        return

    h = abs(hash(f"{lead.get('id')}|{lead.get('property')}|{lead.get('unit')}"))
    flat: list[str] = []
    for i in range(len(_DUMMY_CONCERN_SETS)):
        flat.extend(_DUMMY_CONCERN_SETS[(h + i) % len(_DUMMY_CONCERN_SETS)])
    seen = {x.lower() for x in imp}
    added_any = False
    for s in flat:
        if len(imp) >= target:
            break
        sl = s.lower()
        if sl in seen:
            continue
        imp.append(s)
        seen.add(sl)
        added_any = True
    summary["improvements_or_concerns"] = imp[:6]
    summary["includes_synthetic_tour_concerns"] = bool(added_any or db_n == 0)


def _feedback_improvement_tags_by_property(
    client: Any, since_iso: str, property_ids: set[str]
) -> dict[str, list[str]]:
    if not property_ids:
        return {}
    fp_to_prop: dict[str, str] = {}
    for pid in property_ids:
        try:
            fr = client.table("floorplans").select("id").eq("property_id", pid).limit(400).execute()
            for row in fr.data or []:
                fp_to_prop[str(row["id"])] = str(pid)
        except Exception:
            continue
    if not fp_to_prop:
        return {p: [] for p in property_ids}
    improvements: dict[str, Counter[str]] = {str(p): Counter() for p in property_ids}
    fp_ids = list(fp_to_prop.keys())
    for i in range(0, len(fp_ids), _CHUNK):
        batch = fp_ids[i : i + _CHUNK]
        try:
            r = (
                client.table("feedback")
                .select("floorplan_id,raw_feedback,created_at")
                .in_("floorplan_id", batch)
                .gte("created_at", since_iso)
                .limit(250)
                .execute()
            )
            rows = r.data or []
        except Exception:
            rows = []
        for row in rows:
            fid = str(row.get("floorplan_id") or "")
            prop = fp_to_prop.get(fid)
            if not prop or prop not in improvements:
                continue
            raw = row.get("raw_feedback")
            if not isinstance(raw, dict):
                continue
            for x in raw.get("improvements") or []:
                t = str(x or "").strip()[:120]
                if t:
                    improvements[prop][t] += 1
            c = str(raw.get("additionalCommentsImprovements") or "").strip()
            if len(c) > 12:
                improvements[prop][c[:140]] += 1
    return {str(p): [k for k, _ in improvements[str(p)].most_common(8)] for p in property_ids}


def _build_alternate_unit_catalog(row: dict[str, Any], vacant_units: list[dict[str, Any]]) -> dict[str, Any]:
    """Same-building options plus other communities (vacant inventory) for concern-based matching."""
    prop_name = str(row.get("property") or "")
    my_unit = str(row.get("unit") or "").strip()
    same_property: list[dict[str, Any]] = []
    other_properties: list[dict[str, Any]] = []
    for u in vacant_units:
        uc = str(u.get("unitCode") or "").strip()
        pn = str(u.get("property") or "")
        if not uc or uc == my_unit:
            continue
        entry = {
            "unit": uc,
            "property": pn,
            "unit_type": u.get("unitType"),
            "conv_pct": u.get("conv"),
            "status": u.get("status"),
            "days_vacant": u.get("days"),
        }
        if pn == prop_name:
            if len(same_property) < 6:
                same_property.append(entry)
        else:
            other_properties.append(entry)

    def rank_key(x: dict[str, Any]) -> tuple[int, int]:
        st = str(x.get("status") or "")
        tier = 0 if st == "healthy" else 1 if st == "stale" else 2
        return (tier, int(x.get("days_vacant") or 999))

    other_properties.sort(key=rank_key)
    other_properties = other_properties[:12]
    return {"same_property": same_property, "other_properties": other_properties}


def _cache_key(
    lead_slice: list[dict[str, Any]],
    vacant_units: list[dict[str, Any]],
    since_iso: str,
    fb_digest: list[dict[str, Any]],
) -> str:
    vd = sorted(
        {
            (
                str(u.get("unitCode")),
                str(u.get("property")),
                str(u.get("conv")),
            )
            for u in vacant_units[:60]
        }
    )
    raw = json.dumps(
        {"leads": fb_digest, "vac": vd, "since": since_iso},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(raw.encode()).hexdigest()[:48]


def _apply_heuristic_fallback(lead_rows: list[dict[str, Any]]) -> None:
    for r in lead_rows:
        r["recommended_action"] = r.get("recommended_action") or (
            "Follow up while interest is fresh; reference their tour and offer to answer questions."
        )
        if not r.get("objections"):
            heat = str(r.get("status") or "")
            r["objections"] = (
                ["Move-in timing", "Budget / rent expectations"]
                if heat != "cold"
                else ["Re-engagement — confirm interest"]
            )
        if not r.get("alternates"):
            r["alternates"] = [
                "Review other available homes—same community or nearby properties—that better match what they asked about on tour."
            ]
        if not r.get("ai_draft"):
            r["ai_draft"] = (
                f"Hi {r.get('name')}, thanks for touring {r.get('property')} ({r.get('unit')}). "
                "I’d love to follow up and share a couple of options that might be an even better fit. When’s a good time to connect?"
            )


_SYSTEM = """You enrich multifamily leasing "lead prioritization" cards. Prospects toured and need follow-up. Output valid JSON only.

For EACH object in input.leads, output one matching object in output.enrichments (same "id", same order).

Data meaning:
- tour_booking_ids / tour_floorplan_ids: scope of their most recent tour; feedback rows are pre-filtered to this booking and/or floorplan when possible.
- tour_feedback_from_guest: from the feedback table for this guest, scoped to that tour. Fields include improvements_or_concerns (use as Tour objections). If includes_synthetic_tour_concerns is true, some lines are representative placeholders because no DB row matched yet—still treat them as the guest's stated concerns (no fake quotes beyond that).
- alternate_units_catalog: real vacant units. same_property = other units at the community they toured. other_properties = vacant units at OTHER named properties in the catalog. You MUST only recommend alternates that appear in this catalog (unit + property strings).

Rules:
1) objections: 2–4 short phrases (≤90 chars). MUST prioritize tour_feedback_from_guest.improvements_or_concerns (these are the tour objections line—use verbatim or tight paraphrase). You may also reflect free_text_snippets or likes when helpful. Do not replace them with generic "re-engagement" unless includes_synthetic_tour_concerns is true and themes are already the placeholder set.

2) alternates: 2–4 lines. Each line MUST cite a real unit + property from alternate_units_catalog (format like "Unit 4C — Oak Residences, …" using exact unit and property strings from the catalog). Explain in the same line how that option relates to their stated concern or feedback theme (e.g. more light, larger bath, different layout, pet-friendly). Prefer at least one option from other_properties when their feedback suggests a different layout, size, or community fit and the catalog has entries. If catalog is nearly empty, give one honest line to review upcoming availability without inventing units.

3) recommended_action: one imperative (≤320 chars): when/how to follow up (call/SMS/email), what to lead with (their feedback + suggested alternates).

4) ai_draft: one outbound SMS-style message (≤720 chars). Address the guest by name. Mention the property and unit they toured. Briefly acknowledge their concern using tour_feedback_from_guest when present (no fake quotes). Mention at least ONE specific alternate from your alternates list (unit + property) as a suggested next step. Friendly CTA. No markdown.

Return: {"enrichments": [{"id": "...", "recommended_action": "...", "objections": [...], "alternates": [...], "ai_draft": "..."}, ...]}"""


def _openai_enrichments_for_payload_leads(
    payload_leads: list[dict[str, Any]],
    window_days: int,
    api_key: str,
) -> dict[str, dict[str, Any]]:
    """One chat.completions call for a slice of payload_leads; returns id -> enrichment dict."""
    from openai import OpenAI

    if not payload_leads:
        return {}
    user_obj = {"window_days": window_days, "leads": payload_leads}
    body = json.dumps(user_obj, ensure_ascii=True, separators=(",", ":"))
    oai = OpenAI(api_key=api_key, timeout=_lead_card_openai_timeout_sec())
    resp = oai.chat.completions.create(
        model=_openai_model(),
        temperature=0.25,
        max_tokens=_lead_card_max_tokens_for_batch(len(payload_leads)),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": body
                + '\nReturn {"enrichments":[...]} with one entry per lead, same ids and order.',
            },
        ],
    )
    text = (resp.choices[0].message.content or "").strip()
    parsed = json.loads(text) if text else {}
    enrich_list = parsed.get("enrichments")
    if not isinstance(enrich_list, list):
        raise ValueError("missing enrichments")
    by_id: dict[str, dict[str, Any]] = {}
    for item in enrich_list:
        if isinstance(item, dict) and item.get("id"):
            by_id[str(item["id"])] = item
    return by_id


def enrich_leads_summary_rows(
    lead_rows: list[dict[str, Any]],
    vacant_units: list[dict[str, Any]],
    *,
    since_iso: str,
    window_days: int,
) -> None:
    """Mutates each row with recommended_action, objections, alternates, ai_draft. Strips internal keys."""
    if not lead_rows:
        return

    api_key = _openai_key()
    if not api_key or _truthy_env("SKIP_LEAD_CARD_LLM"):
        if _truthy_env("SKIP_LEAD_CARD_LLM") and api_key:
            logger.info("lead_card_llm: SKIP_LEAD_CARD_LLM set; using heuristic copy only")
        heuristic_lead_cards_only(lead_rows)
        return

    try:
        from openai import OpenAI  # noqa: F401
    except ImportError:
        logger.warning("lead_card_llm: openai not installed")
        heuristic_lead_cards_only(lead_rows)
        return

    slice_rows = lead_rows[:_MAX_LEADS_PER_LLM_CALL]
    try:
        client = get_client()
        prospect_ids = [str(r["id"]) for r in slice_rows]
        fb_by_prospect = _feedback_rows_for_prospects(client, prospect_ids)

        prop_ids = {str(r["property_id"]) for r in slice_rows if r.get("property_id")}
        fb_by_property = _feedback_improvement_tags_by_property(client, since_iso, prop_ids)

        payload_leads: list[dict[str, Any]] = []
        fb_digest: list[dict[str, Any]] = []
        for r in slice_rows:
            pr = str(r["id"])
            guest_fb_rows_all = fb_by_prospect.get(pr, [])
            scoped_fb = _scoped_feedback_rows_for_tour(
                guest_fb_rows_all,
                r.get("tour_booking_ids") or [],
                r.get("tour_floorplan_ids") or [],
            )
            guest_summary = _summarize_guest_tour_feedback(scoped_fb)
            _augment_objections_from_dummy_if_sparse(guest_summary, r)
            prop = r.get("property_id")
            community_themes = fb_by_property.get(str(prop), []) if prop else []
            catalog = _build_alternate_unit_catalog(r, vacant_units)
            payload_leads.append(
                {
                    "id": r["id"],
                    "name": r["name"],
                    "property": r["property"],
                    "unit": r["unit"],
                    "heat": r["status"],
                    "priority": r["priority"],
                    "tags": r.get("tags") or [],
                    "tour_time": r["tour_time"],
                    "last_contact": r["last_contact"],
                    "recent_events": r.get("recent_events") or [],
                    "tour_booking_ids": r.get("tour_booking_ids") or [],
                    "tour_floorplan_ids": r.get("tour_floorplan_ids") or [],
                    "tour_feedback_from_guest": guest_summary,
                    "community_feedback_themes": community_themes
                    if guest_summary.get("submission_count", 0) == 0
                    else [],
                    "alternate_units_catalog": catalog,
                }
            )
            fb_digest.append(
                {
                    "id": pr,
                    "sub": guest_summary.get("submission_count", 0),
                    "syn": guest_summary.get("includes_synthetic_tour_concerns", False),
                    "fp": (r.get("tour_floorplan_ids") or [])[:2],
                    "imp": guest_summary.get("improvements_or_concerns", [])[:3],
                }
            )

        ck = _cache_key(slice_rows, vacant_units, since_iso, fb_digest)
        now = time.time()
        ttl = _lead_card_cache_ttl_sec()
        cached = _LEAD_CARD_CACHE.get(ck)
        if cached and (now - cached[0]) <= ttl:
            _merge_enrichments(slice_rows, cached[1])
        else:
            parallel_min = max(4, int(os.getenv("LEAD_CARD_LLM_PARALLEL_MIN", "12") or 12))
            if _truthy_env("LEAD_CARD_LLM_DISABLE_PARALLEL"):
                parallel_min = 10_000
            if len(payload_leads) >= parallel_min:
                mid = len(payload_leads) // 2
                first, second = payload_leads[:mid], payload_leads[mid:]
                with ThreadPoolExecutor(max_workers=2) as pool:
                    f1 = pool.submit(_openai_enrichments_for_payload_leads, first, window_days, api_key)
                    f2 = pool.submit(_openai_enrichments_for_payload_leads, second, window_days, api_key)
                    by_id = {**f1.result(), **f2.result()}
            else:
                by_id = _openai_enrichments_for_payload_leads(payload_leads, window_days, api_key)
            _LEAD_CARD_CACHE[ck] = (now, by_id)
            _merge_enrichments(slice_rows, by_id)
    except Exception as e:
        logger.warning("lead_card_llm enrichment skipped: %s", e)
        _apply_heuristic_fallback(slice_rows)

    for r in lead_rows:
        _apply_heuristic_fallback([r])

    _strip_internal_lead_fields(lead_rows)


def _merge_enrichments(rows: list[dict[str, Any]], by_id: dict[str, dict[str, Any]]) -> None:
    for r in rows:
        e = by_id.get(str(r["id"]))
        if not e:
            _apply_heuristic_fallback([r])
            continue
        ra = e.get("recommended_action")
        if isinstance(ra, str) and ra.strip():
            r["recommended_action"] = ra.strip()[:500]
        obs = e.get("objections")
        if isinstance(obs, list):
            r["objections"] = [str(x).strip()[:200] for x in obs[:6] if str(x).strip()]
        alts = e.get("alternates")
        if isinstance(alts, list):
            r["alternates"] = [str(x).strip()[:280] for x in alts[:6] if str(x).strip()]
        ad = e.get("ai_draft")
        if isinstance(ad, str) and ad.strip():
            r["ai_draft"] = ad.strip()[:900]


def _strip_internal_lead_fields(lead_rows: list[dict[str, Any]]) -> None:
    for r in lead_rows:
        r.pop("recent_events", None)
        r.pop("property_id", None)
        r.pop("tour_booking_ids", None)
        r.pop("tour_floorplan_ids", None)
