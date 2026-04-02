from schemas.property_schema import PropertyCreate
async def create_property(data:PropertyCreate):
    return {'id':'1', **data.dict()}
async def list_properties():
    return []
