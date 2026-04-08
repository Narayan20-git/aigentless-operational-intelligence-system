"""
Aigentless POC — FastAPI Backend
Property Onboarding Module
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from app.routers import onboarding, checklist, generate_content
from app.scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background scheduler on startup
    scheduler = start_scheduler()
    yield
    # Shutdown scheduler on exit
    scheduler.shutdown()

app = FastAPI(
    title="Aigentless — Property Onboarding API",
    description="AI-Powered Leasing Platform — Property Onboarding Module",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(onboarding.router,       prefix="/api/v1", tags=["Onboarding"])
app.include_router(checklist.router,        prefix="/api/v1", tags=["Checklist"])
app.include_router(generate_content.router, prefix="/api/v1", tags=["AI Content"])

@app.get("/health")
async def health():
    return {"status": "ok", "service": "aigentless-onboarding"}
