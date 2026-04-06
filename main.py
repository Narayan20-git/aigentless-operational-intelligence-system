from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi_standalone_docs import StandaloneDocs

from config.database import close_db, startup_database
from routes.lead_routes import router as lead_router
from routes.property_routes import router as property_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_available = await startup_database()
    yield
    await close_db()


app = FastAPI(title="Aigentless Backend", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
StandaloneDocs(app=app)
app.include_router(property_router, prefix="/properties", tags=["Properties"])
app.include_router(lead_router, prefix="/leads", tags=["Leads"])


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs", status_code=307)


@app.get("/doc", include_in_schema=False)
async def doc_typo():
    return RedirectResponse(url="/docs", status_code=307)
