from pydantic import BaseModel
class LeadCreate(BaseModel):
    name:str
class LeadOut(LeadCreate):
    id:str
