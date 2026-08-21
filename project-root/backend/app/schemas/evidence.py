import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BaselineSummary(BaseModel):
    """
    Explainable "normal" for a location, derived from historical ANALYZED
    observations (see baseline_service.py). `available=False` means there
    isn't enough historical data yet — this is NEVER treated as evidence
    of an anomaly, only as "we don't know what's normal here yet".
    """

    model_config = ConfigDict(protected_namespaces=())

    available: bool
    historical_observation_count: int
    turbidity_baseline: Optional[str] = None
    algae_baseline: Optional[str] = None
    waste_rate: Optional[float] = None
    deviates: Optional[bool] = None  # None when no baseline is available


class RelatedObservationSummary(BaseModel):
    """One related report's indicators + how it relates to the evaluated report."""

    model_config = ConfigDict(protected_namespaces=())

    report_id: uuid.UUID
    distance_meters: float
    minutes_apart: float
    algae_indicator: Optional[str] = None
    color_anomaly: Optional[str] = None
    turbidity_indicator: Optional[str] = None
    visible_waste: Optional[bool] = None
    image_quality: Optional[str] = None


class EvidenceFusionResult(BaseModel):
    """
    The fused, explainable evidence assessment for a single report. Never a
    diagnosis or outbreak prediction — `condition_summary` and
    `recommended_action` are deliberately scoped to observable environmental
    anomaly language, with human officer verification as the only action.
    """

    report_id: uuid.UUID
    confidence_score: float  # 0.0 - 1.0
    confidence_level: str  # LOW | MODERATE | HIGH
    condition_summary: str
    related_report_count: int
    supporting_observations: list[RelatedObservationSummary]
    conflicting_observations: list[RelatedObservationSummary]
    baseline: BaselineSummary
    evidence_reasons: list[str]
    recommended_action: str
