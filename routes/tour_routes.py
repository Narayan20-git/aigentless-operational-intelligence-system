from fastapi import APIRouter
from schemas.tour_schema import TourCreate, TourOut
from services.tour_service import create_tour, list_tours
router=APIRouter()
@router.post('/',response_model=TourOut)
async def create(data:TourCreate):
    return await create_tour(data)
@router.get('/',response_model=list[TourOut])
async def list_all():
    return await list_tours()
