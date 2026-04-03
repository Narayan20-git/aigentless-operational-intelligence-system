from schemas.booking_schema import BookingCreate
async def create_booking(data:BookingCreate):
    return {'id':'1', **data.dict()}
async def list_bookings():
    return []
