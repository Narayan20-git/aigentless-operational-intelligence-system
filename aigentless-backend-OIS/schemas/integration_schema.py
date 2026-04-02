from pydantic import BaseModel
class IntegrationCreate(BaseModel):
    name:str
class IntegrationOut(IntegrationCreate):
    id:str
