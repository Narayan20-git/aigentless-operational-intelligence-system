import asyncio
import os
import json
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

from config.database import get_client


def _fetch_properties() -> list[dict[str, Any]]:
    response = get_client().table("properties").select("*").execute()
    return response.data or []


async def list_properties() -> list[dict[str, Any]]:
    return await asyncio.to_thread(_fetch_properties)


def _count_prospect_events_in_window(property_id: Optional[str], days: int) -> int:
    from services.dashboard_service import normalize_dashboard_days

    d = normalize_dashboard_days(days)
    since = (datetime.now(UTC) - timedelta(days=d)).isoformat()
    client = get_client()
    try:
        q = client.table("prospect_events").select("id", count="exact").gte("timestamp", since)
        if property_id:
            q = q.eq("property_id", property_id)
        r = q.limit(1).execute()
        return int(r.count or 0)
    except Exception:
        return 0


def _fetch_onboarding_summary(property_id: Optional[str] = None, days: int = 7) -> dict[str, Any]:
    query = get_client().table("property_onboarding_status").select("*")
    if property_id:
        query = query.eq("property_id", property_id)

    res = query.execute()
    rows = res.data or []

    ready       = sum(1 for r in rows if r.get("status") == "ready")
    in_progress = sum(1 for r in rows if r.get("status") == "in-progress")
    blocked     = sum(1 for r in rows if r.get("status") == "blocked")
    avg_pct     = round(sum(r.get("overall_completeness", 0) for r in rows) / len(rows)) if rows else 0
    events_n = _count_prospect_events_in_window(property_id, days)

    return {
        "ready_to_launch":    ready,
        "in_progress":        in_progress,
        "blocked":            blocked,
        "avg_completeness":   avg_pct,
        "total_properties":   len(rows),
        "prospect_events_in_window": events_n,
        "days":               days,
    }


async def get_onboarding_summary(property_id: Optional[str] = None, days: int = 7) -> dict[str, Any]:
    from services.dashboard_service import normalize_dashboard_days

    d = normalize_dashboard_days(days)
    return await asyncio.to_thread(_fetch_onboarding_summary, property_id, d)


def _fetch_onboarding_properties(property_id: Optional[str] = None, status: Optional[str] = None) -> dict[str, Any]:
    client = get_client()
    
    # Get properties
    prop_query = client.table("properties").select(
        "id, name, description, units, go_live_date"
    )
    if property_id:
        prop_query = prop_query.eq("id", property_id)
    props = prop_query.execute().data or []

    # Get onboarding status
    status_query = client.table("property_onboarding_status").select("*")
    if property_id:
        status_query = status_query.eq("property_id", property_id)
    if status:
        status_query = status_query.eq("status", status)
    statuses = {r["property_id"]: r for r in (status_query.execute().data or [])}

    # Get unresolved blockers
    blockers_res = client.table("property_onboarding_blockers") \
        .select("property_id, message, severity") \
        .eq("resolved", False) \
        .execute()
    blockers_map: dict = {}
    for b in (blockers_res.data or []):
        blockers_map.setdefault(b["property_id"], []).append(b["message"])

    # Build response
    result = []
    for p in props:
        pid = p["id"]
        st  = statuses.get(pid, {})
        if status and st.get("status") != status:
            continue
        result.append({
            "property_id":          pid,
            "name":                 p["name"],
            "status":               st.get("status", "in-progress"),
            "overall_completeness": st.get("overall_completeness", 0),
            "blockers":             blockers_map.get(pid, []),
            "last_updated":         p.get("updated_at"), # Properties might not have updated_at according to the select but keeping as POC
            "go_live_date":         p.get("go_live_date"),
        })

    return {"properties": result, "total": len(result)}


async def list_onboarding_properties(property_id: Optional[str] = None, status: Optional[str] = None) -> dict[str, Any]:
    return await asyncio.to_thread(_fetch_onboarding_properties, property_id, status)


def _section(sections: dict, key: str) -> dict:
    s = sections.get(key, {})
    return {
        "completion_pct": s.get("completion_pct", 0),
        "status":         s.get("status", "not-started"),
        "metadata":       s.get("metadata", {}),
    }


def _fetch_onboarding_detail(property_id: str) -> Optional[dict[str, Any]]:
    client = get_client()

    # Property info
    try:
        prop_res = client.table("properties") \
            .select("id, name, description, units, year_built, website, amenities, go_live_date") \
            .eq("id", property_id) \
            .single() \
            .execute()
    except Exception:
        return None

    if not prop_res.data:
        return None
    prop = prop_res.data

    # Onboarding status
    try:
        status_res = client.table("property_onboarding_status") \
            .select("*") \
            .eq("property_id", property_id) \
            .single() \
            .execute()
        status = status_res.data or {}
    except Exception:
        status = {}

    # All 6 sections
    sections_res = client.table("property_onboarding_sections") \
        .select("section, completion_pct, status, metadata, updated_at") \
        .eq("property_id", property_id) \
        .execute()
    sections = {s["section"]: s for s in (sections_res.data or [])}

    # Active blockers
    blockers_res = client.table("property_onboarding_blockers") \
        .select("section, severity, message, description, action, ai_can_fix") \
        .eq("property_id", property_id) \
        .eq("resolved", False) \
        .execute()
    blockers = blockers_res.data or []

    return {
        "property": {
            "id":          prop.get("id"),
            "name":        prop.get("name"),
            "description": prop.get("description"),
            "units":       prop.get("units"),
            "year_built":  prop.get("year_built"),
            "website":     prop.get("website"),
        },
        "onboarding": {
            "overall_completeness": status.get("overall_completeness", 0),
            "status":               status.get("status", "in-progress"),
            "last_calculated_at":   status.get("last_calculated_at"),
        },
        "sections": {
            "property_info":     _section(sections, "property_info"),
            "units_floor_plans": _section(sections, "units_floor_plans"),
            "amenities":         _section(sections, "amenities"),
            "media_photos":      _section(sections, "media_photos"),
            "content_faqs":      _section(sections, "content_faqs"),
            "integrations":      _section(sections, "integrations"),
        },
        "blockers": blockers,
    }


async def get_onboarding_detail(property_id: str) -> Optional[dict[str, Any]]:
    return await asyncio.to_thread(_fetch_onboarding_detail, property_id)


CHECKLIST_ITEMS = {
    "property_info": [
        {"key": "name",             "label": "Property name",          "required": True},
        {"key": "description",      "label": "Property description",   "required": True},
        {"key": "address",          "label": "Property address",       "required": True},
        {"key": "units",            "label": "Total units",            "required": True},
        {"key": "year_built",       "label": "Year built",             "required": True},
        {"key": "website",          "label": "Website URL",            "required": True},
        {"key": "amenities",        "label": "Amenities list",         "required": True},
        {"key": "go_live_date",     "label": "Go-live date",           "required": False},
        {"key": "parking",          "label": "Parking details",        "required": False},
        {"key": "virtual_tour_url", "label": "Virtual tour URL",       "required": False},
        {"key": "office_hours",     "label": "Office hours",           "required": False},
        {"key": "accessibility",    "label": "Accessibility features", "required": False},
    ],
    "units_floor_plans": [
        {"key": "units_added",      "label": "All units added",             "required": True},
        {"key": "bedrooms",         "label": "Bedroom/bathroom counts",     "required": True},
        {"key": "square_footage",   "label": "Square footage per unit",     "required": True},
        {"key": "floor_plans",      "label": "Floor plan PDFs uploaded",    "required": True},
        {"key": "pricing",          "label": "Unit pricing entered",        "required": True},
    ],
    "amenities": [
        {"key": "amenities_list",   "label": "Amenities list complete",         "required": True},
        {"key": "descriptions",     "label": "All amenity descriptions written","required": True},
        {"key": "photos",           "label": "Amenity photos uploaded",         "required": False},
    ],
    "media_photos": [
        {"key": "exterior",         "label": "Property exterior photos",    "required": True},
        {"key": "common_areas",     "label": "Lobby/common area photos",    "required": True},
        {"key": "unit_photos",      "label": "All unit photos uploaded",    "required": True},
        {"key": "virtual_tour",     "label": "Virtual tour link added",     "required": False},
    ],
    "content_faqs": [
        {"key": "general",          "label": "General leasing FAQ",                    "required": True},
        {"key": "pet_policy",       "label": "Pet policy FAQ",                         "required": True},
        {"key": "parking",          "label": "Parking FAQ",                            "required": True},
        {"key": "utilities",        "label": "Utility billing FAQ",                    "required": True},
        {"key": "maintenance",      "label": "Maintenance request process",            "required": True},
        {"key": "guest",            "label": "Guest policy",                           "required": True},
        {"key": "noise",            "label": "Noise policy",                           "required": True},
        {"key": "lease",            "label": "Lease renewal terms",                    "required": True},
        {"key": "move_in",          "label": "Move-in checklist",                      "required": True},
        {"key": "general_2",        "label": "Renter's insurance requirements",        "required": True},
        {"key": "general_3",        "label": "Short-term rental policy",               "required": False},
        {"key": "lease_2",          "label": "Lease break policy",                     "required": False},
    ],
    "integrations": [
        {"key": "apartments_com",   "label": "Apartments.com connected",           "required": True},
        {"key": "zillow",           "label": "Zillow Rental Manager connected",    "required": True},
        {"key": "yardi",            "label": "Yardi Voyager / PMS synced",         "required": True},
        {"key": "rent_com",         "label": "Rent.com connected",                 "required": False},
        {"key": "appfolio",         "label": "AppFolio connected",                 "required": False},
    ],
}

def _get_completed_keys(property_id: str, section: str) -> set:
    client = get_client()
    completed = set()

    if section == "property_info":
        prop = client.table("properties") \
            .select("name,description,address,units,year_built,website,amenities,go_live_date,parking") \
            .eq("id", property_id).single().execute().data or {}
        if prop.get("name"):            completed.add("name")
        if prop.get("description"):     completed.add("description")
        if prop.get("address"):         completed.add("address")
        if prop.get("units"):           completed.add("units")
        if prop.get("year_built"):      completed.add("year_built")
        if prop.get("website"):         completed.add("website")
        if prop.get("amenities"):       completed.add("amenities")
        if prop.get("go_live_date"):    completed.add("go_live_date")
        if prop.get("parking"):         completed.add("parking")

    elif section == "units_floor_plans":
        units = client.table("units") \
            .select("id,monthly_rent") \
            .eq("property_id", property_id).execute().data or []
        fps   = client.table("floorplans") \
            .select("id,square_footage") \
            .eq("property_id", property_id).execute().data or []
        if units:                          completed.add("units_added")
        if any(u.get("monthly_rent") for u in units): completed.add("pricing")
        if fps:                            completed.add("floor_plans")
        if any(f.get("square_footage") for f in fps): completed.add("square_footage")
        if fps:                            completed.add("bedrooms")

    elif section == "amenities":
        amenities = client.table("property_amenities") \
            .select("name,description") \
            .eq("property_id", property_id).execute().data or []
        if amenities:                            completed.add("amenities_list")
        if all(a.get("description") for a in amenities): completed.add("descriptions")

    elif section == "media_photos":
        prop_imgs = client.table("property_images") \
            .select("id,image_path") \
            .eq("property_id", property_id).execute().data or []
        unit_imgs = client.table("unit_images") \
            .select("id").execute().data or []
        if any("exterior" in img.get("image_path","") for img in prop_imgs): completed.add("exterior")
        if any("lobby" in img.get("image_path","") for img in prop_imgs):    completed.add("common_areas")
        if unit_imgs:                            completed.add("unit_photos")

    elif section == "content_faqs":
        faqs = client.table("property_faqs") \
            .select("category,answer,is_published") \
            .eq("property_id", property_id) \
            .eq("is_published", True).execute().data or []
        published_cats = {f.get("category") for f in faqs if f.get("answer")}
        category_map = {
            "general":     ["general", "general_2", "general_3"],
            "pet_policy":  ["pet_policy"],
            "parking":     ["parking"],
            "utilities":   ["utilities"],
            "maintenance": ["maintenance"],
            "guest":       ["guest"],
            "noise":       ["noise"],
            "lease":       ["lease", "lease_2"],
            "move_in":     ["move_in"],
        }
        for cat, keys in category_map.items():
            if cat in published_cats:
                completed.update(keys)

    elif section == "integrations":
        integrations = client.table("property_integration_status") \
            .select("integration_name,status") \
            .eq("property_id", property_id) \
            .eq("status", "connected").execute().data or []
        completed.update(i.get("integration_name") for i in integrations)

    return completed

def _build_section_checklist(property_id: str, section: str) -> dict:
    if section not in CHECKLIST_ITEMS:
        return {}
        
    items_template = CHECKLIST_ITEMS[section]
    completed_keys = _get_completed_keys(property_id, section)
    items = []
    for item in items_template:
        items.append({
            "key":       item["key"],
            "label":     item["label"],
            "required":  item["required"],
            "completed": item["key"] in completed_keys,
        })
    completed = sum(1 for i in items if i["completed"])
    return {
        "items":          items,
        "completed":      completed,
        "total":          len(items),
        "completion_pct": round(completed / len(items) * 100) if items else 0,
    }

def _fetch_full_checklist(property_id: str) -> Optional[dict[str, Any]]:
    client = get_client()
    try:
        prop = client.table("properties") \
            .select("id, name") \
            .eq("id", property_id) \
            .single() \
            .execute()
    except Exception:
        return None

    if not prop.data:
        return None

    checklist = {}
    for section in CHECKLIST_ITEMS.keys():
        checklist[section] = _build_section_checklist(property_id, section)

    total_items     = sum(len(v.get("items", [])) for v in checklist.values())
    completed_items = sum(
        sum(1 for i in v.get("items", []) if i["completed"])
        for v in checklist.values()
    )

    return {
        "property_id":       property_id,
        "property_name":     prop.data.get("name"),
        "checklist":         checklist,
        "summary": {
            "total_items":     total_items,
            "completed_items": completed_items,
            "pending_items":   total_items - completed_items,
            "overall_pct":     round(completed_items / total_items * 100) if total_items else 0,
        }
    }

def _fetch_section_checklist(property_id: str, section: str) -> Optional[dict[str, Any]]:
    if section not in CHECKLIST_ITEMS:
        return None # handled in route as 400

    client = get_client()
    try:
        prop = client.table("properties") \
            .select("id, name") \
            .eq("id", property_id) \
            .single() \
            .execute()
    except Exception:
        return {"error": "not_found"}

    if not prop.data:
        return {"error": "not_found"}

    return {
        "property_id":   property_id,
        "property_name": prop.data.get("name"),
        "section":       section,
        "checklist":     _build_section_checklist(property_id, section),
    }

async def get_full_checklist(property_id: str) -> Optional[dict[str, Any]]:
    return await asyncio.to_thread(_fetch_full_checklist, property_id)

async def get_section_checklist(property_id: str, section: str) -> Optional[dict[str, Any]]:
    return await asyncio.to_thread(_fetch_section_checklist, property_id, section)


def _fetch_ai_jobs(property_id: str) -> list[dict[str, Any]]:
    client = get_client()
    jobs = client.table("property_ai_content_jobs") \
        .select("*") \
        .eq("property_id", property_id) \
        .order("created_at", desc=True) \
        .execute()
    return jobs.data or []


def _fetch_ai_job(property_id: str, job_id: str) -> Optional[dict[str, Any]]:
    client = get_client()
    try:
        job = client.table("property_ai_content_jobs") \
            .select("*") \
            .eq("id", job_id) \
            .eq("property_id", property_id) \
            .single().execute()
        return job.data
    except Exception:
        return None


def _create_ai_job_record(property_id: str, section: str, content_type: str, triggered_by: Optional[str]) -> str:
    client = get_client()
    job = client.table("property_ai_content_jobs").insert({
        "property_id":   property_id,
        "section":       section,
        "content_type":  content_type,
        "status":        "pending",
        "triggered_by":  triggered_by,
    }).execute()
    return job.data[0]["id"]


async def get_all_ai_jobs(property_id: str) -> list[dict[str, Any]]:
    return await asyncio.to_thread(_fetch_ai_jobs, property_id)


async def get_single_ai_job(property_id: str, job_id: str) -> Optional[dict[str, Any]]:
    return await asyncio.to_thread(_fetch_ai_job, property_id, job_id)


async def create_new_ai_job(property_id: str, section: str, content_type: str, triggered_by: Optional[str]) -> str:
    return await asyncio.to_thread(_create_ai_job_record, property_id, section, content_type, triggered_by)


def run_generation_task(job_id: str, property_id: str, section: str, content_type: str):
    """
    Synchronous background task — PREVIEW ONLY mode.

    Generates content using AI and stores it in generated_content field
    for the frontend to display as a preview.

    Nothing is saved to property_faqs, property_amenities, or properties.
    No blockers are resolved. No completeness is recalculated.
    The user must explicitly confirm to save (handled separately).
    """
    client = get_client()
    try:
        # Mark as running
        client.table("property_ai_content_jobs") \
            .update({"status": "running"}) \
            .eq("id", job_id).execute()

        # Get property context
        prop = client.table("properties") \
            .select("name, description, units, year_built, amenities, address, housing_type") \
            .eq("id", property_id).single().execute().data or {}

        # For FAQs: query property_faqs directly to find categories with empty/missing answers
        # This gives the AI the exact missing categories instead of a vague blocker message
        missing_faq_categories: list[str] = []
        if content_type == "faq":
            all_faqs = client.table("property_faqs") \
                .select("category, answer, is_published") \
                .eq("property_id", property_id).execute().data or []

            published_with_answer = {
                f["category"] for f in all_faqs
                if f.get("is_published") and f.get("answer", "").strip()
            }

            # All required FAQ categories from the checklist
            all_required_categories = [
                "general", "pet_policy", "parking", "utilities",
                "maintenance", "guest", "noise", "lease", "move_in",
            ]
            missing_faq_categories = [
                c for c in all_required_categories
                if c not in published_with_answer
            ]

        # Get RAG context from other properties' published FAQs
        rag_context = _get_rag_context(client, property_id, content_type)

        # Build prompt with specific missing categories (not vague blocker messages)
        prompt = _build_prompt(prop, content_type, missing_faq_categories, rag_context)

        # Generate content via OpenAI — PREVIEW ONLY, nothing saved to DB
        generated = _call_gemini(prompt, content_type)

        # Store generated preview in job record only — no other DB writes
        client.table("property_ai_content_jobs").update({
            "status":            "completed",
            "prompt_used":       prompt,
            "generated_content": generated,
            "completed_at":      "now()",
        }).eq("id", job_id).execute()

    except Exception as e:
        client.table("property_ai_content_jobs").update({
            "status":        "failed",
            "error_message": str(e),
            "completed_at":  "now()",
        }).eq("id", job_id).execute()


def _get_rag_context(client, property_id: str, content_type: str) -> str:
    try:
        similar = client.table("property_faqs") \
            .select("question, answer, category") \
            .eq("is_published", True) \
            .neq("property_id", property_id) \
            .neq("answer", "") \
            .limit(10).execute().data or []

        if not similar:
            return ""

        context_lines = ["Similar content from other properties:"]
        for faq in similar[:5]:
            context_lines.append(f"Q: {faq['question']}\\nA: {faq['answer']}")
        return "\\n\\n".join(context_lines)
    except Exception:
        return ""


def _build_prompt(prop: dict, content_type: str, missing_items: list, rag_context: str) -> str:
    prop_context = f"Property: {prop.get('name', 'Unknown')}\\n"
    prop_context += f"Type: {prop.get('housing_type', 'apartment')}\\n"
    prop_context += f"Units: {prop.get('units', 'N/A')}\\n"
    prop_context += f"Year built: {prop.get('year_built', 'N/A')}\\n"
    prop_context += f"Location: {json.dumps(prop.get('address', {}))}\\n"
    prop_context += f"Amenities: {', '.join(prop.get('amenities', [])[:10])}\\n"

    if content_type == "faq":
        # missing_items is a list of specific category names e.g. ["pet_policy", "parking", "lease"]
        category_labels = {
            "general":     "General leasing / renters insurance",
            "pet_policy":  "Pet policy (breeds, weight, deposit, monthly pet rent)",
            "parking":     "Parking (assigned spaces, cost, guest parking)",
            "utilities":   "Utility billing (what is included vs resident responsibility)",
            "maintenance": "Maintenance request process (how to submit, response time)",
            "guest":       "Guest policy (overnight stays, duration limits)",
            "noise":       "Noise policy (quiet hours, rules)",
            "lease":       "Lease renewal terms (notice period, renewal process)",
            "move_in":     "Move-in process (scheduling, checklist, key handover)",
        }

        if missing_items:
            category_lines = "\\n".join(
                f'- Category "{c}": {category_labels.get(c, c)}'
                for c in missing_items
            )
            missing_str = f"Generate exactly ONE FAQ entry for EACH of these {len(missing_items)} missing categories:\\n{category_lines}"
        else:
            missing_str = "Generate comprehensive FAQ content covering all standard categories."

        return f"You are a property management content specialist.\\nGenerate professional FAQ answers for a rental property.\\n\\n{prop_context}\\n\\n{missing_str}\\n\\n{rag_context}\\n\\nReturn ONLY a valid JSON array — one object per category — in this exact format, no other text:\\n[\\n  {{\"question\": \"What is the pet policy?\", \"answer\": \"...\", \"category\": \"pet_policy\"}}\\n]\\n\\nRules:\\n- category field must exactly match the category name provided above\\n- answer must be 2-4 sentences, professional, and specific to this property\\n- do NOT generate FAQs for categories not listed above"

    elif content_type == "amenity_description":
        amenities = prop.get("amenities", [])
        return f"You are a property management content specialist.\\nGenerate compelling descriptions for apartment amenities.\\n\\n{prop_context}\\n\\nGenerate descriptions for ALL amenities listed.\\nReturn ONLY a valid JSON array, no other text:\\n[\\n  {{\"name\": \"Pool\", \"description\": \"...\", \"category\": \"outdoor\"}}\\n]\\n\\nCategories: outdoor, indoor, pet, parking, tech, wellness, general\\nDescriptions must be 1-2 sentences, compelling, and specific."

    elif content_type == "property_description":
        return f"You are a property management content specialist.\\nWrite a compelling property description for a rental listing.\\n\\n{prop_context}\\n\\nWrite a professional 3-4 sentence property description.\\nReturn ONLY a JSON object, no other text:\\n{{\"description\": \"...\"}}\\n\\nThe description should highlight key features and location benefits."

    return f"Generate {content_type} for {prop.get('name', 'this property')}."


def _call_gemini(prompt: str, content_type: str) -> dict:
    """
    Generate content using OpenAI gpt-4.1-mini.
    Named _call_gemini for backward compatibility.
    Returns parsed JSON — never saves to DB.
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a property management content specialist. "
                        "Return ONLY valid JSON — no markdown, no explanation, no code fences."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=2048,
        )
        text = response.choices[0].message.content.strip()
        # Strip markdown fences if model adds them anyway
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {e}", "raw": text if "text" in dir() else ""}
    except Exception as e:
        return {"error": str(e)}


def _save_generated_content(client, property_id: str, content_type: str, generated: dict):
    if content_type == "faq" and isinstance(generated, list):
        for faq in generated:
            if not faq.get("question") or not faq.get("answer"):
                continue
            existing = client.table("property_faqs") \
                .select("id") \
                .eq("property_id", property_id) \
                .eq("category", faq.get("category", "general")) \
                .eq("is_published", False).execute().data

            if existing:
                client.table("property_faqs").update({
                    "answer":       faq["answer"],
                    "ai_generated": True,
                    "is_published": True,
                    "updated_at":   "now()",
                }).eq("id", existing[0]["id"]).execute()
            else:
                client.table("property_faqs").insert({
                    "property_id":  property_id,
                    "question":     faq["question"],
                    "answer":       faq["answer"],
                    "category":     faq.get("category", "general"),
                    "ai_generated": True,
                    "is_published": True,
                }).execute()

    elif content_type == "amenity_description" and isinstance(generated, list):
        for amenity in generated:
            if not amenity.get("name") or not amenity.get("description"):
                continue
            existing = client.table("property_amenities") \
                .select("id") \
                .eq("property_id", property_id) \
                .eq("name", amenity["name"]).execute().data

            if existing:
                client.table("property_amenities").update({
                    "description": amenity["description"],
                    "ai_generated": True,
                    "updated_at":  "now()",
                }).eq("id", existing[0]["id"]).execute()
            else:
                client.table("property_amenities").insert({
                    "property_id":  property_id,
                    "name":         amenity["name"],
                    "description":  amenity["description"],
                    "category":     amenity.get("category", "general"),
                    "ai_generated": True,
                }).execute()

    elif content_type == "property_description" and isinstance(generated, dict):
        if generated.get("description"):
            client.table("properties").update({
                "description": generated["description"],
                "updated_at":  "now()",
            }).eq("id", property_id).execute()


def _resolve_blockers(client, property_id: str, section: str):
    client.table("property_onboarding_blockers").update({
        "resolved":    True,
        "resolved_at": "now()",
    }).eq("property_id", property_id) \
      .eq("section", section) \
      .eq("ai_can_fix", True) \
      .eq("resolved", False).execute()
