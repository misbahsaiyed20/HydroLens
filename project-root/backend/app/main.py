"""
Aqua Sentinel API — Sprint 1: database foundation + report submission.

Startup uses Base.metadata.create_all() rather than Alembic. This is a brand
new project with no data to preserve, so create_all is the fastest path to a
working schema; switch to Alembic migrations once the schema is verified and
starts changing incrementally (Sprint 2+).
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import Base, engine
from app.models import *  # noqa: F401,F403 - ensures every model is registered on Base before create_all
from app.api.reports import router as reports_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Directory must exist before StaticFiles mounts it (mounting happens at
# import time, before the lifespan startup hook runs).
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

# Serve uploaded images so the frontend can render report photos directly,
# e.g. GET /uploads/<filename>.
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

app.include_router(reports_router, prefix=settings.api_prefix)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.app_name}
