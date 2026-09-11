import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VerificationRequest(BaseModel):
    """
    Body for POST /reports/{report_id}/verify. `status` only accepts
    VERIFIED or REJECTED — UNVERIFIED is the default state a report starts
    in, not something this endpoint sets (submitting it is a validation
    error, which is exactly the "422 -> invalid verification request"
    behavior the spec asks for; Pydantic/FastAPI produces that
    automatically for a Literal type, no extra code needed).

    `verifier_reference` now comes from the AUTHENTICATED reviewer
    (current_user.email, set server-side in the /verify route) — never
    trusted from the client. It's optional here only so a client-supplied
    value is accepted for backward compatibility with direct API callers;
    the route always overwrites it with the real authenticated identity
    before this reaches the service layer, so the audit trail can't be
    spoofed by whatever a caller puts in the request body.
    """

    status: Literal["VERIFIED", "REJECTED"]
    verifier_reference: Optional[str] = Field(default=None, max_length=200)
    note: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("verifier_reference")
    @classmethod
    def not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("verifier_reference cannot be blank")
        return v.strip() if v else v


class VerificationEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    report_id: uuid.UUID
    event_type: str
    previous_status: str
    new_status: str
    verifier_reference: str
    note: Optional[str] = None
    created_at: datetime


class VerificationHistoryOut(BaseModel):
    """Response for both POST /verify and GET /verification — the current
    state plus the full append-only history that produced it."""

    report_id: uuid.UUID
    verification_status: str  # current state: UNVERIFIED | VERIFIED | REJECTED
    latest_verifier_reference: Optional[str] = None
    latest_verified_at: Optional[datetime] = None
    latest_note: Optional[str] = None
    history: list[VerificationEventOut]


class EvidenceProvenanceSummary(BaseModel):
    """
    Breaks supporting/conflicting related reports down by verification
    status, so evidence output can distinguish "AI-only" from "human-
    verified" evidence without changing confidence_service's score at all
    (see evidence_fusion_service.py — this is purely descriptive).
    """

    evaluated_report_verification_status: str
    supporting_verified_count: int
    supporting_unverified_count: int
    supporting_rejected_count: int
    conflicting_verified_count: int
    conflicting_unverified_count: int
    conflicting_rejected_count: int
