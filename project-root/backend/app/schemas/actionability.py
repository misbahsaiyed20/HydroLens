import uuid

from pydantic import BaseModel

from app.schemas.evidence import BaselineSummary


class ActionabilityResult(BaseModel):
    """
    Operational recommendation derived FROM an existing EvidenceFusionResult
    — this schema never carries medical/diagnostic fields. `action_level` is
    an operational review priority, not a health outcome, and
    `recommended_action` always resolves to either continued monitoring or
    a human officer review (never an automatic decision).
    """

    report_id: uuid.UUID
    confidence_score: float
    confidence_level: str  # LOW | MODERATE | HIGH
    exposure_risk_level: str  # LOW | MODERATE | ELEVATED
    action_level: str  # CONTINUE_MONITORING | REVIEW_RECOMMENDED | PRIORITY_REVIEW
    recommended_action: str
    key_reasons: list[str]
    supporting_report_count: int
    conflicting_report_count: int
    baseline: BaselineSummary
