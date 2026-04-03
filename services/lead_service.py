from schemas.lead_schema import LeadCreate
async def create_lead(data:LeadCreate):
    return {'id':'1', **data.dict()}
async def list_leads():
    return []
