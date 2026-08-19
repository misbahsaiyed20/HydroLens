import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Observation(Base):
    """
    Structured indicators extracted from a Report's photo. One-to-one with
    Report. Sprint 1 only creates the table/relationship — the AI vision
    service that actually populates these fields is a later sprint, so every
    field here is nullable and this row is not created during report
    submission yet.

    Deliberately NOT over-engineered: just the flat indicator fields called
    out in the spec, no scoring/weighting logic yet (that belongs to
    confidence_service later).
    """
    __tablename__ = "observations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False, unique=True)

    algae_indicator = Column(String(50), nullable=True)      # e.g. "none" | "low" | "moderate" | "high"
    color_anomaly = Column(String(50), nullable=True)        # e.g. observed off-color description
    visible_waste = Column(Boolean, nullable=True)
    turbidity_indicator = Column(String(50), nullable=True)  # e.g. "clear" | "cloudy" | "opaque"
    image_quality = Column(String(50), nullable=True)        # e.g. "good" | "blurry" | "poor_lighting"
    model_confidence = Column(Float, nullable=True)          # 0.0-1.0, confidence of the vision model itself

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    report = relationship("Report", back_populates="observation")
