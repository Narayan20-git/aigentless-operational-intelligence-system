from fastapi import APIRouter
from schemas.integration_schema import IntegrationCreate, IntegrationOut
from services.integration_service import create_integration, list_integrations
router=APIRouter()
@router.post('/',response_model=IntegrationOut)
async def create(data:IntegrationCreate):
    return await create_integration(data)
@router.get('/',response_model=list[IntegrationOut])
async def list_all():
    return await list_integrations()
