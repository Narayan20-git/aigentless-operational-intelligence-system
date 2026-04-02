from pydantic import BaseModel
class TourCreate(BaseModel):
    name:str
class TourOut(TourCreate):
    id:str
