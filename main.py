from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi_standalone_docs import StandaloneDocs

from config.database import close_db, db_is_ready, startup_database
from routes.chatbot_routes import router as chatbot_router
from routes.dashboard_routes import router as dashboard_router
from routes.property_routes import router as property_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_available = await startup_database()
    yield
    await close_db()


app = FastAPI(title="Aigentless Backend", lifespan=lifespan)
# CORS: any browser origin. Wildcard requires allow_credentials=False (FastAPI/Starlette).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
StandaloneDocs(app=app)
app.include_router(dashboard_router, prefix="/api", tags=["Dashboard APIs"])
app.include_router(property_router, prefix="/properties", tags=["Properties"])
app.include_router(chatbot_router, prefix="/api", tags=["Chatbot"])


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs", status_code=307)


@app.get("/doc", include_in_schema=False)
async def doc_typo():
    return RedirectResponse(url="/docs", status_code=307)


@app.get("/health")
async def health():
    return {"status": "ok", "db_available": getattr(app.state, "db_available", False), "db_ready": db_is_ready()}
