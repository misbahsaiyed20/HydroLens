import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.enums import ReportStatus, VerificationStatus
from app.schemas.location import LocationOut
from app.schemas.observation import ObservationOut


class ReportCreate(BaseModel):
    """
    Fields sent alongside the image in the multipart POST /api/reports request.
    (The image itself is a separate UploadFile param on the endpoint, not part
    of this schema — FastAPI can't validate a file through a JSON body field.)
    """
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    stream_name: Optional[str] = Field(default=None, max_length=200)
    stream_segment: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("stream_name", "stream_segment", "description")
    @classmethod
    def blank_to_none(cls, v):
        if v is not None and not v.strip():
            return None
        return v


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    image_path: str
    description: Optional[str] = None
    status: ReportStatus
    # Sprint 5: deliberately separate from `status` above — `status` is AI
    # analysis progress, this is human review state. See VerificationStatus
    # docstring. Never conflate the two.
    verification_status: VerificationStatus
    submitted_at: datetime
    updated_at: datetime
    location: LocationOut
    observation: Optional[ObservationOut] = None


class ReportListOut(BaseModel):
    total: int
    items: list[ReportOut]
