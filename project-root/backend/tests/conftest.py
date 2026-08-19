"""
Test DB: SQLite instead of Postgres, so tests run anywhere with no external
DB dependency. This is fine for Sprint 1 (no Postgres-only types like
ARRAY/JSONB are used yet) — revisit if later sprints need Postgres-specific
features.

IMPORTANT: DATABASE_URL is overridden via env var BEFORE app.main is
imported, so the app's own engine (app.database.engine) never tries to
reach a real Postgres server during tests.
"""
import os
import uuid

import pytest

# Must happen before any `app.*` import triggers app.config/app.database.
os.environ["DATABASE_URL"] = "sqlite:///./test_aqua_sentinel.db"
os.environ["UPLOAD_DIR"] = "test_uploads"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.models import *  # noqa: F401,F403 - register all models on Base
from app.main import app


@pytest.fixture()
def db_session(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # test DB file + uploads land in a throwaway dir

    engine = create_engine(
        "sqlite:///./test_aqua_sentinel.db",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
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
