from pydantic import BaseModel
class BookingCreate(BaseModel):
    name:str
class BookingOut(BookingCreate):
    id:str
