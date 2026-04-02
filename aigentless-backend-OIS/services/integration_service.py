from schemas.integration_schema import IntegrationCreate
async def create_integration(data:IntegrationCreate):
    return {'id':'1', **data.dict()}
async def list_integrations():
    return []
