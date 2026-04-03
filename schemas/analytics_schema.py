from pydantic import BaseModel
class AnalyticsCreate(BaseModel):
    name:str
class AnalyticsOut(AnalyticsCreate):
    id:str
