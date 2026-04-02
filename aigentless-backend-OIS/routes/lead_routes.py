from fastapi import APIRouter
from schemas.lead_schema import LeadCreate, LeadOut
from services.lead_service import create_lead, list_leads
router=APIRouter()
@router.post('/',response_model=LeadOut)
async def create(data:LeadCreate):
    return await create_lead(data)
@router.get('/',response_model=list[LeadOut])
async def list_all():
    return await list_leads()
