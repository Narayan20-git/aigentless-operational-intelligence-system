from fastapi import FastAPI
from routes.property_routes import router as property_router
app=FastAPI(title='Aigentless Backend')
app.include_router(property_router,prefix='/properties',tags=['Properties'])
