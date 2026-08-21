"""
Report.submitted_at is stored as plain DateTime (no explicit timezone type).
SQLite drops tzinfo entirely on round-trip, and Postgres's default
TIMESTAMP WITHOUT TIME ZONE does the same — so a value read back from the
DB is naive even though it was written as tz-aware UTC. Comparing that
against a fresh `datetime.now(timezone.utc)` raises a naive/aware
TypeError unless both sides are normalized first. These two helpers do
that consistently everywhere Sprint 3 does time-delta math.
"""
from datetime import datetime, timezone


def to_naive_utc(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
