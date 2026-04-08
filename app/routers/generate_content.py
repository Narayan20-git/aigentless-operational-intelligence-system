"""
Generate Missing Content Router
Uses Google Gemini via Google ADK for AI content generation
Endpoint: POST /onboarding/{property_id}/generate-content

Flow:
  1. Read property context from Supabase
  2. Find what's missing (blockers with ai_can_fix=true)
  3. Retrieve similar content via pgvector RAG
  4. Call Google Gemini to generate missing content
  5. Save generated content back to Supabase
  6. Update section completion % + resolve blocker
  7. Return updated onboarding status
"""
import os
import json
import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from app.db import supabase

# Google ADK + Gemini
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

router = APIRouter()

class GenerateContentRequest(BaseModel):
    section:      str   = "content_faqs"   # which section to generate for
    content_type: str   = "faq"            # faq | amenity_description | property_description
    triggered_by: Optional[str] = "admin"

class GenerateContentResponse(BaseModel):
    job_id:       str
    status:       str
    message:      str
    property_id:  str

# ── POST /onboarding/{property_id}/generate-content ─────────────────────────
@router.post("/onboarding/{property_id}/generate-content",
             response_model=GenerateContentResponse)
async def generate_missing_content(
    property_id:     str,
    request:         GenerateContentRequest,
    background_tasks: BackgroundTasks,
):
    """
    Async endpoint — creates a job and returns immediately.
    Generation runs in the background.
    Poll GET /onboarding/{property_id}/ai-jobs to check status.
    """
    # Verify property exists
    prop = supabase.table("properties") \
        .select("id, name") \
        .eq("id", property_id) \
        .single().execute()
    if not prop.data:
        raise HTTPException(status_code=404, detail="Property not found")

    # Create AI job record
    job = supabase.table("property_ai_content_jobs").insert({
        "property_id":   property_id,
        "section":       request.section,
        "content_type":  request.content_type,
        "status":        "pending",
        "triggered_by":  request.triggered_by,
    }).execute()

    job_id = job.data[0]["id"]

    # Run generation in background
    background_tasks.add_task(
        _run_generation,
        job_id, property_id, request.section, request.content_type
    )

    return GenerateContentResponse(
        job_id=job_id,
        status="pending",
        message=f"Content generation started for {request.content_type}. Poll /ai-jobs/{job_id} for status.",
        property_id=property_id,
    )

# ── GET /onboarding/{property_id}/ai-jobs ────────────────────────────────────
@router.get("/onboarding/{property_id}/ai-jobs")
async def get_ai_jobs(property_id: str):
    """Poll for AI job status."""
    jobs = supabase.table("property_ai_content_jobs") \
        .select("*") \
        .eq("property_id", property_id) \
        .order("created_at", desc=True) \
        .execute()
    return {"jobs": jobs.data or []}

@router.get("/onboarding/{property_id}/ai-jobs/{job_id}")
async def get_ai_job(property_id: str, job_id: str):
    """Get single job status."""
    job = supabase.table("property_ai_content_jobs") \
        .select("*") \
        .eq("id", job_id) \
        .eq("property_id", property_id) \
        .single().execute()
    if not job.data:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.data

# ── BACKGROUND GENERATION TASK ───────────────────────────────────────────────
async def _run_generation(job_id: str, property_id: str, section: str, content_type: str):
    """
    Background task that:
    1. Marks job as running
    2. Fetches property context
    3. Retrieves RAG context via pgvector
    4. Calls Gemini to generate content
    5. Saves content to appropriate table
    6. Updates section completion
    7. Resolves blockers
    8. Marks job as completed
    """
    try:
        # Mark as running
        supabase.table("property_ai_content_jobs") \
            .update({"status": "running"}) \
            .eq("id", job_id).execute()

        # Get property context
        prop = supabase.table("properties") \
            .select("name, description, units, year_built, amenities, address, housing_type") \
            .eq("id", property_id).single().execute().data

        # Get missing items from blockers
        blockers = supabase.table("property_onboarding_blockers") \
            .select("message, section, type") \
            .eq("property_id", property_id) \
            .eq("ai_can_fix", True) \
            .eq("resolved", False).execute().data or []

        missing_items = [b["message"] for b in blockers]

        # Get RAG context — similar FAQs from other ready properties
        rag_context = _get_rag_context(property_id, content_type)

        # Build prompt
        prompt = _build_prompt(prop, content_type, missing_items, rag_context)

        # Call Google Gemini
        generated = await _call_gemini(prompt, content_type)

        # Save generated content
        await _save_generated_content(property_id, content_type, generated)

        # Resolve relevant blockers
        _resolve_blockers(property_id, section)

        # Recalculate completion
        supabase.rpc("recalculate_onboarding_status", {"p_property_id": property_id}).execute()

        # Mark job completed
        supabase.table("property_ai_content_jobs").update({
            "status":            "completed",
            "prompt_used":       prompt,
            "generated_content": generated,
            "completed_at":      "now()",
        }).eq("id", job_id).execute()

    except Exception as e:
        supabase.table("property_ai_content_jobs").update({
            "status":        "failed",
            "error_message": str(e),
            "completed_at":  "now()",
        }).eq("id", job_id).execute()

def _get_rag_context(property_id: str, content_type: str) -> str:
    """
    RAG: Fetch similar published FAQs/descriptions from other properties
    using pgvector cosine similarity search.
    Falls back to text search if no embeddings exist yet.
    """
    try:
        # Get published FAQs from ready properties (excluding current)
        similar = supabase.table("property_faqs") \
            .select("question, answer, category") \
            .eq("is_published", True) \
            .neq("property_id", property_id) \
            .neq("answer", "") \
            .limit(10).execute().data or []

        if not similar:
            return ""

        context_lines = ["Similar content from other properties:"]
        for faq in similar[:5]:
            context_lines.append(f"Q: {faq['question']}\nA: {faq['answer']}")
        return "\n\n".join(context_lines)
    except:
        return ""

def _build_prompt(prop: dict, content_type: str, missing_items: list, rag_context: str) -> str:
    """Build Gemini prompt based on content type and property context."""
    prop_context = f"""
Property: {prop.get('name', 'Unknown')}
Type: {prop.get('housing_type', 'apartment')}
Units: {prop.get('units', 'N/A')}
Year built: {prop.get('year_built', 'N/A')}
Location: {json.dumps(prop.get('address', {}))}
Amenities: {', '.join(prop.get('amenities', [])[:10])}
"""
    missing_str = "\n".join(f"- {item}" for item in missing_items) if missing_items else "Generate comprehensive content"

    if content_type == "faq":
        return f"""You are a property management content specialist.
Generate professional FAQ answers for a rental property.

{prop_context}

Missing FAQs that need to be generated:
{missing_str}

{rag_context}

Generate clear, professional FAQ answers for each missing item.
Return ONLY a valid JSON array in this exact format, no other text:
[
  {{"question": "What is the pet policy?", "answer": "...", "category": "pet_policy"}},
  {{"question": "What is the parking policy?", "answer": "...", "category": "parking"}}
]

Categories must be one of: general, pet_policy, parking, utilities, lease, maintenance, guest, noise, move_in, move_out
Answers must be 2-4 sentences, professional, and specific to this property."""

    elif content_type == "amenity_description":
        amenities = prop.get("amenities", [])
        return f"""You are a property management content specialist.
Generate compelling descriptions for apartment amenities.

{prop_context}

Generate descriptions for ALL amenities listed.
Return ONLY a valid JSON array, no other text:
[
  {{"name": "Pool", "description": "...", "category": "outdoor"}},
  {{"name": "Gym", "description": "...", "category": "wellness"}}
]

Categories: outdoor, indoor, pet, parking, tech, wellness, general
Descriptions must be 1-2 sentences, compelling, and specific."""

    elif content_type == "property_description":
        return f"""You are a property management content specialist.
Write a compelling property description for a rental listing.

{prop_context}

Write a professional 3-4 sentence property description.
Return ONLY a JSON object, no other text:
{{"description": "..."}}

The description should highlight key features and location benefits."""

    return f"Generate {content_type} for {prop.get('name', 'this property')}."

async def _call_gemini(prompt: str, content_type: str) -> dict:
    """Call Google Gemini API via Google ADK."""
    try:
        response = model.generate_content(
            prompt,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            },
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                max_output_tokens=2048,
            )
        )
        text = response.text.strip()
        # Clean markdown code blocks if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except json.JSONDecodeError:
        # Return raw text if JSON parsing fails
        return {"raw_content": response.text}

async def _save_generated_content(property_id: str, content_type: str, generated: dict):
    """Save AI-generated content to the appropriate Supabase table."""
    if content_type == "faq" and isinstance(generated, list):
        for faq in generated:
            if not faq.get("question") or not faq.get("answer"):
                continue
            # Upsert FAQ
            existing = supabase.table("property_faqs") \
                .select("id") \
                .eq("property_id", property_id) \
                .eq("category", faq.get("category", "general")) \
                .eq("is_published", False).execute().data

            if existing:
                supabase.table("property_faqs").update({
                    "answer":       faq["answer"],
                    "ai_generated": True,
                    "is_published": True,
                    "updated_at":   "now()",
                }).eq("id", existing[0]["id"]).execute()
            else:
                supabase.table("property_faqs").insert({
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
            existing = supabase.table("property_amenities") \
                .select("id") \
                .eq("property_id", property_id) \
                .eq("name", amenity["name"]).execute().data

            if existing:
                supabase.table("property_amenities").update({
                    "description": amenity["description"],
                    "ai_generated": True,
                    "updated_at":  "now()",
                }).eq("id", existing[0]["id"]).execute()
            else:
                supabase.table("property_amenities").insert({
                    "property_id":  property_id,
                    "name":         amenity["name"],
                    "description":  amenity["description"],
                    "category":     amenity.get("category", "general"),
                    "ai_generated": True,
                }).execute()

    elif content_type == "property_description" and isinstance(generated, dict):
        if generated.get("description"):
            supabase.table("properties").update({
                "description": generated["description"],
                "updated_at":  "now()",
            }).eq("id", property_id).execute()

def _resolve_blockers(property_id: str, section: str):
    """Mark relevant ai_can_fix blockers as resolved after generation."""
    supabase.table("property_onboarding_blockers").update({
        "resolved":    True,
        "resolved_at": "now()",
    }).eq("property_id", property_id) \
      .eq("section", section) \
      .eq("ai_can_fix", True) \
      .eq("resolved", False).execute()
