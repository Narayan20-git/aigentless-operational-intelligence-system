from fastapi import APIRouter
from schemas.analytics_schema import AnalyticsCreate, AnalyticsOut
from services.analytics_service import create_analytics, list_analyticss
router=APIRouter()
@router.post('/',response_model=AnalyticsOut)
async def create(data:AnalyticsCreate):
    return await create_analytics(data)
@router.get('/',response_model=list[AnalyticsOut])
async def list_all():
    return await list_analyticss()
