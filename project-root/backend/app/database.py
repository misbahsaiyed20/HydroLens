"""
SQLAlchemy engine/session setup.

Sprint 1 uses `Base.metadata.create_all()` on startup for speed, since this is
a brand-new project with no data to preserve. Once the schema stabilizes
(after Sprint 1 is verified working), swap this for Alembic migrations so
future schema changes (e.g. adding evidence-fusion tables) are tracked
properly instead of relying on create_all.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import get_settings

settings = get_settings()

# `pool_pre_ping` avoids stale-connection errors on long-lived dev sessions.
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
