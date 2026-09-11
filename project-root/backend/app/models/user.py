import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import UserRole


class User(Base):
    """
    Citizen/reviewer account. `password_hash` and `role` were added for
    authentication (see app/core/security.py); both are nullable-safe for
    backward compatibility with any pre-auth row (`Report.user_id` was, and
    remains, nullable — anonymous historical reports are untouched and stay
    readable). Any row created through POST /auth/signup always has
    role=CITIZEN and a non-null password_hash; REVIEWER accounts are only
    created via the controlled bootstrap path (scripts/create_reviewer.py),
    never through public signup.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name = Column(String(120), nullable=True)
    email = Column(String(255), unique=True, nullable=True, index=True)

    # Nullable so any legacy/anonymous row (created before auth existed)
    # remains valid without a backfill. A row with no password_hash simply
    # cannot log in — it is not treated as a security hole.
    password_hash = Column(String(255), nullable=True)
    role = Column(SAEnum(UserRole), default=UserRole.CITIZEN, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    reports = relationship("Report", back_populates="user")
