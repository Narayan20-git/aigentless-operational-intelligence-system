from fastapi import APIRouter
from schemas.booking_schema import BookingCreate, BookingOut
from services.booking_service import create_booking, list_bookings
router=APIRouter()
@router.post('/',response_model=BookingOut)
async def create(data:BookingCreate):
    return await create_booking(data)
@router.get('/',response_model=list[BookingOut])
async def list_all():
    return await list_bookings()
