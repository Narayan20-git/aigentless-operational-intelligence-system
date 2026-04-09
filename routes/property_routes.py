from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query, BackgroundTasks
from pydantic import BaseModel

from config.database import db_is_ready, startup_database
from services.property_service import (
    list_properties, 
    get_onboarding_summary, 
    list_onboarding_properties, 
    get_onboarding_detail,
    get_full_checklist,
    get_section_checklist,
    get_all_ai_jobs,
    get_single_ai_job,
    create_new_ai_job,
    run_generation_task,
)

class GenerateContentRequest(BaseModel):
    section:      str   = "content_faqs"   # which section to generate for
    content_type: str   = "faq"            # faq | amenity_description | property_description
    triggered_by: Optional[str] = "admin"

class GenerateContentResponse(BaseModel):
    job_id:       str
    status:       str
    message:      str
    property_id:  str


async def require_supabase(request: Request) -> None:
    if not getattr(request.app.state, "db_available", False):
        request.app.state.db_available = await startup_database()
    if not request.app.state.db_available and db_is_ready():
        request.app.state.db_available = True
    if not request.app.state.db_available:
        raise HTTPException(
            status_code=503,
            detail="Supabase unavailable. Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY/SUPABASE_KEY.",
        )


router = APIRouter(dependencies=[Depends(require_supabase)])


@router.get("/", response_model=list[dict[str, Any]])
async def list_all():
    return await list_properties()


@router.get("/onboarding/summary", response_model=dict[str, Any])
async def get_onboarding_summary_route(property_id: Optional[str] = Query(None)):
    """
    Powers the 4 KPI cards at the top of the screen:
    Ready to launch | In progress | Blocked | Avg. completeness
    Optional ?property_id filter for the dropdown
    """
    return await get_onboarding_summary(property_id)


@router.get("/onboarding", response_model=dict[str, Any])
async def list_onboarding_properties_route(
    property_id: Optional[str] = Query(None),
    status:      Optional[str] = Query(None),
):
    """
    Powers the left panel properties list.
    Returns all properties with their onboarding status + active blockers.
    Optional filters: ?property_id= or ?status=blocked|in-progress|ready
    """
    return await list_onboarding_properties(property_id, status)


@router.get("/onboarding/{property_id}", response_model=dict[str, Any])
async def get_onboarding_detail_route(property_id: str):
    """
    Powers the right panel when a property is selected.
    Returns property detail + all 6 section scores + blockers.
    """
    detail = await get_onboarding_detail(property_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Property not found")
    return detail


@router.get("/onboarding/{property_id}/checklist", response_model=dict[str, Any])
async def get_full_checklist_route(property_id: str):
    """
    View Detailed Checklist button — returns all 6 sections
    with item-level completion status for the property.
    """
    data = await get_full_checklist(property_id)
    if not data:
        raise HTTPException(status_code=404, detail="Property not found")
    return data


@router.get("/onboarding/{property_id}/checklist/{section}", response_model=dict[str, Any])
async def get_section_checklist_route(property_id: str, section: str):
    """Single section checklist — used when clicking on a specific section bar."""
    data = await get_section_checklist(property_id, section)
    if not data:
        raise HTTPException(status_code=400, detail=f"Invalid section: {section}")
    if data.get("error") == "not_found":
        raise HTTPException(status_code=404, detail="Property not found")
        
    return data


@router.post("/onboarding/{property_id}/generate-content", response_model=GenerateContentResponse)
async def generate_missing_content(
    property_id: str,
    request: GenerateContentRequest,
    background_tasks: BackgroundTasks,
):
    """
    Async endpoint — creates a job and returns immediately.
    Generation runs in the background.
    """
    # Verify property exists
    detail = await get_onboarding_detail(property_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Property not found")

    job_id = await create_new_ai_job(
        property_id, 
        request.section, 
        request.content_type, 
        request.triggered_by
    )

    background_tasks.add_task(
        run_generation_task,
        job_id, property_id, request.section, request.content_type
    )

    return GenerateContentResponse(
        job_id=job_id,
        status="pending",
        message=f"Content generation started for {request.content_type}. Poll /ai-jobs/{job_id} for status.",
        property_id=property_id,
    )


@router.get("/onboarding/{property_id}/ai-jobs", response_model=list[dict[str, Any]])
async def get_ai_jobs_route(property_id: str):
    """Poll for AI job status."""
    return await get_all_ai_jobs(property_id)


@router.get("/onboarding/{property_id}/ai-jobs/{job_id}", response_model=dict[str, Any])
async def get_ai_job_route(property_id: str, job_id: str):
    """Get single job status."""
    job = await get_single_ai_job(property_id, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
