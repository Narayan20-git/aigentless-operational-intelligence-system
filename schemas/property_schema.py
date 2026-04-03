from pydantic import BaseModel
class PropertyCreate(BaseModel):
    name:str
    city:str
class PropertyOut(PropertyCreate):
    id:str
