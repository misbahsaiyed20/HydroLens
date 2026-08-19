import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Location(Base):
    """
    Where a report was made. Sprint 1 creates a new Location row per report
    (no deduplication/clustering yet). Deduping nearby coordinates into a
    shared "monitoring point" is baseline_service's job in a later sprint —
    doing it now would be over-engineering ahead of that design.
    """
    __tablename__ = "locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    stream_name = Column(String(200), nullable=True)
    stream_segment = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    reports = relationship("Report", back_populates="location")
