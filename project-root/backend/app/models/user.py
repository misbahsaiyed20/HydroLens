import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """
    Minimal citizen-reporter identity. Sprint 1 has no auth system, so this
    table exists to support the `Report.user_id` relationship, but
    `Report.user_id` is nullable — a report can be submitted anonymously.
    Proper auth (login, sessions/JWT) is intentionally deferred to a later
    sprint per the "no sophisticated authentication yet" instruction.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name = Column(String(120), nullable=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    reports = relationship("Report", back_populates="user")
