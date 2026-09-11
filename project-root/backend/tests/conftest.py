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
# Fixed test-only signing secret. Auth tests need a real secret to sign/verify
# against; production must set its own via JWT_SECRET_KEY (see .env.example)
# — this value is never used outside the test process.
os.environ["JWT_SECRET_KEY"] = "test-only-signing-secret-not-for-production-use"

from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.database import Base, engine, SessionLocal, get_db
from app.models import *  # noqa: F401,F403 - register all models on Base
from app.models.enums import UserRole
from app.models.user import User
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


def _make_user(db_session, *, role, email):
    user = User(email=email, display_name=role.value.title(), password_hash=hash_password("Passw0rd!"), role=role)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def reviewer_user(db_session):
    return _make_user(db_session, role=UserRole.REVIEWER, email="reviewer@example.com")


@pytest.fixture()
def citizen_user(db_session):
    return _make_user(db_session, role=UserRole.CITIZEN, email="citizen@example.com")


@pytest.fixture()
def client(db_session, reviewer_user):
    """
    Default test client. Pre-authenticated as a REVIEWER by default: nearly
    every existing (pre-auth) test in this suite exercises dashboard/cases/
    verification/report endpoints assuming unrestricted access, which is
    exactly what a reviewer has post-auth. This keeps the large existing
    test suite green without touching each test file individually — new
    auth/authorization-specific tests use `anon_client`/`citizen_client`
    below instead, where the lack of privilege is the point being tested.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        token = create_access_token(reviewer_user.id, reviewer_user.role.value)
        test_client.headers["Authorization"] = f"Bearer {token}"
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def anon_client(db_session):
    """Unauthenticated client — no Authorization header at all."""
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
def citizen_client(db_session, citizen_user):
    """Authenticated as a CITIZEN — used to assert reviewer-only endpoints reject citizens."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        token = create_access_token(citizen_user.id, citizen_user.role.value)
        test_client.headers["Authorization"] = f"Bearer {token}"
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
