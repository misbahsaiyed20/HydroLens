import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import VerificationStatus


class VerificationEvent(Base):
    """
    One immutable row per verification action taken on a report. This table
    deliberately serves double duty as BOTH the "verification record" and
    the "audit trail" the spec describes as separate concepts — they turned
    out to need the exact same fields (who, what changed, when, why), so a
    second table would just be the first one copied. `Report.verification_status`
    holds the current/latest state for fast reads; this table holds the
    full history of how it got there.

    Append-only: rows are never updated after creation (hence no
    `updated_at` — including one would misleadingly imply rows can change).
    `previous_status` is always recorded explicitly (read from the report
    at the moment of the change) rather than left null, so every row always
    answers "what did this change from" without needing to look at the
    prior row.

    `verifier_reference` is a plain string, NOT a foreign key to a User/
    officer identity table — there is no authenticated officer/user system
    in this project yet. This is intentionally lightweight (e.g. a name or
    email typed into the request) so the schema doesn't pretend to have
    identity verification it doesn't have. See README limitations.
    """
    __tablename__ = "verification_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False, index=True)

    event_type = Column(String(50), nullable=False, default="VERIFICATION")

    previous_status = Column(SAEnum(VerificationStatus), nullable=False)
    new_status = Column(SAEnum(VerificationStatus), nullable=False)

    verifier_reference = Column(String(200), nullable=False)
    note = Column(String(2000), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    report = relationship("Report", back_populates="verification_events")
