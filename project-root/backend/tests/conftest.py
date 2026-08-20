"""
Test DB: SQLite instead of Postgres, so tests run anywhere with no external
DB dependency. This is fine for Sprint 1/2 (no Postgres-only types like
ARRAY/JSONB are used yet) — revisit if later sprints need Postgres-specific
features.

IMPORTANT: DATABASE_URL is set to a single fixed, absolute-path SQLite file
BEFORE app.main is imported. This matters because the background analysis
task (analyze_report_task) opens its own DB session via app.database's
module-level SessionLocal, completely separate from the request's session —
if tests used a different engine/file than that module-level one, the
background task would write to a different database than the test asserts
against. Using one fixed file for the whole test session, reset between
tests, keeps both paths pointed at the same data.
"""
import os
import tempfile
import uuid
from pathlib import Path

import pytest

_TEST_DB_PATH = Path(tempfile.gettempdir()) / f"aqua_sentinel_test_{uuid.uuid4().hex}.db"

# Must happen before any `app.*` import triggers app.config/app.database.
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"
os.environ["UPLOAD_DIR"] = str(Path(tempfile.gettempdir()) / "aqua_sentinel_test_uploads")
os.environ["GEMINI_API_KEY"] = "test-key-not-real"

from fastapi.testclient import TestClient

from app.database import Base, engine, SessionLocal, get_db
from app.models import *  # noqa: F401,F403 - register all models on Base
from app.main import app


@pytest.fixture()
def db_session():
    """
    Resets the schema before each test (drop + create) so tests don't leak
    state, then hands back a session bound to the SAME engine the app (and
    the background analysis task) uses.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_image_bytes():
    # Minimal valid 1x1 PNG, good enough for upload-validation tests.
    return bytes.fromhex(
        "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753"
        "de0000000c4944415478da6360606060000000050001a5f645400000000049454e44ae426082"
    )


@pytest.fixture(autouse=True)
def block_real_gemini_calls(monkeypatch):
    """
    Safety net so tests never hit the real Gemini API. Any test that needs
    a specific Gemini response should monkeypatch `httpx.post` in
    app.services.vision_service itself (see test_analysis.py) — this
    fixture just ensures an un-mocked test fails fast with a network error
    (caught as VisionAnalysisError, reverting the report to SUBMITTED)
    rather than making a real outbound call.
    """
    import httpx

    def _blocked_post(*args, **kwargs):
        raise httpx.ConnectError("network calls are blocked in tests")

    monkeypatch.setattr("app.services.vision_service.httpx.post", _blocked_post)
