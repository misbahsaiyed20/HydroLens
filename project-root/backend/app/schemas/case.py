import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.evidence import BaselineSummary, RelatedObservationSummary
from app.schemas.location import LocationOut
from app.schemas.observation import ObservationOut
from app.schemas.verification import VerificationEventOut


class CaseSummary(BaseModel):
    report_id: uuid.UUID
    image_path: str
    location: LocationOut
    condition_summary: str
    confidence_score: float
    confidence_level: str
    exposure_risk_level: str
    action_level: str
    verification_status: str
    supporting_count: int
    conflicting_count: int
    created_at: datetime
    updated_at: datetime


class CaseListResult(BaseModel):
    total: int
    items: list[CaseSummary]


class CaseDetail(BaseModel):
    report_id: uuid.UUID
    image_path: str
    status: str
    verification_status: str
    location: LocationOut
    observation: Optional[ObservationOut] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    condition_summary: str
    confidence_score: float
    confidence_level: str
    indicator_severity: str
    exposure_risk_level: str
    action_level: str
    recommended_action: str

    supporting_observations: list[RelatedObservationSummary]
    conflicting_observations: list[RelatedObservationSummary]
    evidence_reasons: list[str]
    baseline: BaselineSummary

    verification_history: list[VerificationEventOut]

    fhir_url: str
