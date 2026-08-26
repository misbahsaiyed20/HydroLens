import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import ReportStatus, VerificationStatus


class Report(Base):
    """
    A single citizen-submitted observation of a stream: one photo + optional
    description, tied to a Location. This is the row the rest of the pipeline
    (analyze_report -> evidence_fusion -> case creation) will eventually hang
    off of. For Sprint 1, it only supports create/read.
    """
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Nullable: anonymous citizen reporting is allowed until real auth exists.
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)

    image_path = Column(String(500), nullable=False)  # relative path under UPLOAD_DIR
    description = Column(String(2000), nullable=True)

    status = Column(SAEnum(ReportStatus), default=ReportStatus.SUBMITTED, nullable=False)

    # Sprint 5: separate from `status` above on purpose — `status` tracks AI
    # analysis progress, this tracks HUMAN review. See VerificationStatus
    # docstring. Every report starts UNVERIFIED and stays that way unless a
    # POST /verify call changes it — nothing in the AI pipeline touches this.
    verification_status = Column(
        SAEnum(VerificationStatus), default=VerificationStatus.UNVERIFIED, nullable=False
    )

    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="reports")
    location = relationship("Location", back_populates="reports")
    observation = relationship(
        "Observation", back_populates="report", uselist=False, cascade="all, delete-orphan"
    )
    verification_events = relationship(
        "VerificationEvent", back_populates="report",
        order_by="VerificationEvent.created_at", cascade="all, delete-orphan"
    )
