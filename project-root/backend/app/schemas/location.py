import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    latitude: float
    longitude: float
    stream_name: Optional[str] = None
    stream_segment: Optional[str] = None
    created_at: datetime
