import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ObservationOut(BaseModel):
    # protected_namespaces=() silences Pydantic's warning about the
    # `model_confidence` field name colliding with its reserved `model_` prefix.
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: uuid.UUID
    algae_indicator: Optional[str] = None
    color_anomaly: Optional[str] = None
    visible_waste: Optional[bool] = None
    turbidity_indicator: Optional[str] = None
    image_quality: Optional[str] = None
    model_confidence: Optional[float] = None
    created_at: datetime
