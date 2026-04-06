from fastapi import APIRouter, Depends, HTTPException, Query, Request

from schemas.lead_schema import LeadCreate, LeadOut, LeadsSummaryResponse
from services.lead_service import create_lead, get_leads_summary, list_leads


async def require_mongodb(request: Request) -> None:
    if not getattr(request.app.state, "db_available", False):
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Check MONGO_URL / MongoDB is running, or DB_OPTIONAL_STARTUP.",
        )


router = APIRouter(dependencies=[Depends(require_mongodb)])


@router.get(
    "/summary",
    response_model=LeadsSummaryResponse,
    summary="UI-ready leads for tabs and cards",
)
async def leads_summary():
    return await get_leads_summary()


@router.get("/", response_model=list[LeadOut])
async def list_all(
    status: str | None = Query(default=None, description="Filter: Hot, Warm, Cold"),
):
    return await list_leads(status=status)


@router.post("/", response_model=LeadOut)
async def create(data: LeadCreate):
    return await create_lead(data)
