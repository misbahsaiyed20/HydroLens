import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ExploreObservationOut(BaseModel):
    id: uuid.UUID
    stream_name: Optional[str] = None
    image_path: str
    condition_summary: str
    turbidity_indicator: Optional[str] = None
    algae_indicator: Optional[str] = None
    visible_waste: Optional[bool] = None
    color_anomaly: Optional[str] = None
    image_quality: Optional[str] = None
    verification_status: str
    submitted_at: datetime


class ExploreListOut(BaseModel):
    total: int
    items: list[ExploreObservationOut]
