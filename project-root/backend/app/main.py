"""
Aqua Sentinel API entrypoint. Startup uses Base.metadata.create_all() for
early development; Sprint 7 adds an optional Alembic migration path (see
alembic/) for environments that need controlled schema evolution instead —
create_all remains the default so local/dev setup stays a single command.
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import Base, engine
from app.models import *  # noqa: F401,F403 - ensures every model is registered on Base before create_all
from app.api.auth import router as auth_router
from app.api.reports import router as reports_router
from app.api.dashboard import router as dashboard_router
from app.api.cases import router as cases_router

settings = get_settings()

# Basic structured-ish logging. Deliberately not a distributed tracing
# stack (Phase 5 explicitly says not to) — just clear, greppable messages
# for the events that matter (report lifecycle, AI analysis, verification).
# Log records never include the Gemini API key or any secret — only
# report/observation IDs and status transitions.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("aqua_sentinel")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    logger.info("startup complete (environment=%s)", settings.environment)
    yield


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    # Docs are useful in development but are unauthenticated introspection
    # of the whole API surface — disable in production unless explicitly
    # wanted. No secrets live in the schema either way, but this keeps the
    # attack surface smaller by default.
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Catch-all for anything that isn't an HTTPException (raw SQLAlchemy
    errors, provider errors, programming bugs). The client gets a generic,
    safe message; the real exception — including type and message, which
    can include internal details — goes to the server log only, never the
    response body.
    """
    logger.exception("unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


# Directory must exist before StaticFiles mounts it (mounting happens at
# import time, before the lifespan startup hook runs).
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

# Serve uploaded images so the frontend can render report photos directly,
# e.g. GET /uploads/<filename>.
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(reports_router, prefix=settings.api_prefix)
app.include_router(dashboard_router, prefix=settings.api_prefix)
app.include_router(cases_router, prefix=settings.api_prefix)


@app.get("/health")
def health_check():
    """
    Liveness/readiness signal. Deliberately does NOT check Gemini
    reachability — an optional external provider being briefly down
    should never make this endpoint report unhealthy (Phase 15). No
    secrets or DB credentials are ever included in the response.
    """
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}
