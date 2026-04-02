from schemas.analytics_schema import AnalyticsCreate
async def create_analytics(data:AnalyticsCreate):
    return {'id':'1', **data.dict()}
async def list_analyticss():
    return []
