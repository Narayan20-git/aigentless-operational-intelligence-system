from schemas.tour_schema import TourCreate
async def create_tour(data:TourCreate):
    return {'id':'1', **data.dict()}
async def list_tours():
    return []
