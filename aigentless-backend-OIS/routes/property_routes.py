from fastapi import APIRouter
from schemas.property_schema import PropertyCreate, PropertyOut
from services.property_service import create_property, list_properties
router=APIRouter()
@router.post('/',response_model=PropertyOut)
async def create(data:PropertyCreate):
    return await create_property(data)
@router.get('/',response_model=list[PropertyOut])
async def list_all():
    return await list_properties()
