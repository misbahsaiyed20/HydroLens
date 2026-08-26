"""
Maps a Report + Observation + EvidenceFusionResult to a FHIR-compatible
Observation resource, isolated in this one module so nothing else in the
app is coupled to FHIR structure. This is NOT a FHIR server — no
validation against the full FHIR spec, no persistence, no _history, no
CapabilityStatement. It is a plain dict shaped like a valid FHIR R4
Observation resource, built from data that genuinely exists in this system.

Scientific/data-integrity rules this module follows strictly:
  - `subject` references an environmental LOCATION, never a Patient. This
    is an environmental observation, not a clinical one — FHIR's base
    Observation resource explicitly allows Location (among others) as a
    valid subject type.
  - `status` is always "preliminary": Sprint 4 has no human (officer)
    verification step yet (that's a later sprint), and FHIR's own
    definition of "preliminary" — initial/interim, data may be incomplete
    or unverified — is the honest description of AI-extracted, not-yet-
    reviewed data. Nothing here is marked "final".
  - No LOINC/SNOMED codes are invented. Every `code`/`component.code` uses
    a free-text CodeableConcept.text rather than fabricated coding systems
    this project hasn't actually validated against a terminology server.
  - No patient demographic or identifying fields are populated, because
    none exist in this system — inventing them would violate the "do not
    fabricate data" requirement.

Sprint 5 update — status now reflects verification, still never overclaims:
  - UNVERIFIED (default) -> "preliminary" (unchanged from Sprint 4)
  - VERIFIED   -> "final": FHIR's own definition of "final" is "the
    observation is complete and there are no further actions needed" —
    that's a statement about the DATA'S review status, not a claim that
    the environmental condition is scientifically proven. A human
    confirming "yes, this observation is a reasonable read of the photo"
    is exactly what FHIR "final" describes.
  - REJECTED   -> "cancelled": FHIR's definition — "the result is no
    longer valid and should not be used for any purpose" — matches a
    human reviewer determining this observation shouldn't be treated as
    valid evidence. The underlying photo/report row still exists; only
    its evidentiary status is marked invalid.
  - The verifier's identity (verifier_reference) is deliberately NOT
    included in the resource — it may be a name/email, and this project
    has no policy for what interoperability partners should do with that.
    Only the non-identifying verification_status + timestamp are exposed.
"""
import uuid
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.models.enums import ReportStatus, VerificationStatus
from app.models.report import Report
from app.schemas.evidence import EvidenceFusionResult
from app.services.evidence_fusion_service import (
    ReportNotAnalyzedError,
    ReportNotFoundError,
    get_evidence_for_report,
)

_FHIR_STATUS_BY_VERIFICATION = {
    VerificationStatus.UNVERIFIED: "preliminary",
    VerificationStatus.VERIFIED: "final",
    VerificationStatus.REJECTED: "cancelled",
}


def _round_or_none(value, digits=3):
    return round(value, digits) if value is not None else None


def build_fhir_observation(report: Report, evidence: EvidenceFusionResult) -> dict[str, Any]:
    obs = report.observation
    location = report.location

    components: list[dict[str, Any]] = []

    if obs.turbidity_indicator is not None:
        components.append({"code": {"text": "Turbidity indicator"}, "valueString": obs.turbidity_indicator})
    if obs.algae_indicator is not None:
        components.append({"code": {"text": "Algae indicator"}, "valueString": obs.algae_indicator})
    if obs.visible_waste is not None:
        components.append({"code": {"text": "Visible waste"}, "valueBoolean": obs.visible_waste})
    if obs.color_anomaly is not None:
        components.append({"code": {"text": "Color anomaly"}, "valueString": obs.color_anomaly})
    if obs.image_quality is not None:
        components.append({"code": {"text": "Image quality"}, "valueString": obs.image_quality})
    if obs.model_confidence is not None:
        components.append({
            "code": {"text": "AI vision model confidence"},
            "valueQuantity": {"value": _round_or_none(obs.model_confidence), "unit": "probability (0-1)"},
        })

    # Evidence-fusion outputs, represented as additional components rather
    # than FHIR's coded `interpretation` field — that field expects values
    # from a defined FHIR value set (e.g. Normal/Abnormal/High), and this
    # project's LOW/MODERATE/HIGH confidence scale isn't a validated mapping
    # to that set. Free-text components avoid overclaiming a standard
    # meaning this data doesn't actually have.
    components.append({
        "code": {"text": "Evidence-fusion confidence score"},
        "valueQuantity": {"value": evidence.confidence_score, "unit": "score (0-1)"},
    })
    components.append({"code": {"text": "Evidence-fusion confidence level"}, "valueString": evidence.confidence_level})
    components.append({"code": {"text": "Related report count"}, "valueInteger": evidence.related_report_count})

    # Sprint 5: verification status as a component (non-identifying — the
    # verifier's name/email is deliberately excluded, see module docstring).
    components.append({"code": {"text": "Verification status"}, "valueString": report.verification_status.value})

    notes = [{"text": evidence.condition_summary}]
    latest_event = report.verification_events[-1] if report.verification_events else None
    if report.verification_status == VerificationStatus.VERIFIED and latest_event is not None:
        notes.append({"text": f"Human-verified on {latest_event.created_at.isoformat()}Z."})
    elif report.verification_status == VerificationStatus.REJECTED and latest_event is not None:
        notes.append({"text": f"Marked rejected on human review on {latest_event.created_at.isoformat()}Z."})

    subject_display = "Unknown stream location"
    if location is not None:
        subject_display = f"Stream location ({location.latitude}, {location.longitude})"
        if location.stream_name:
            subject_display += f" — {location.stream_name}"

    resource: dict[str, Any] = {
        "resourceType": "Observation",
        "id": str(report.id),
        "identifier": [{"system": "urn:aqua-sentinel:report-id", "value": str(report.id)}],
        "status": _FHIR_STATUS_BY_VERIFICATION[report.verification_status],
        "category": [{"text": "Environmental monitoring — citizen-reported stream observation"}],
        "code": {"text": "Citizen-reported urban stream environmental observation"},
        "subject": {"display": subject_display},
        "effectiveDateTime": report.submitted_at.isoformat() + "Z",
        "issued": report.updated_at.isoformat() + "Z",
        "component": components,
        "note": notes,
    }

    return resource


def get_fhir_observation_for_report(db: Session, report_id: uuid.UUID) -> dict[str, Any]:
    """Fetches the report + its evidence-fusion result and builds the FHIR
    resource. Reuses evidence_fusion_service's exceptions so the API layer
    handles /evidence, /actionability, and /fhir identically for
    not-found/not-analyzed cases."""
    report = (
        db.query(Report)
        .options(
            joinedload(Report.location),
            joinedload(Report.observation),
            joinedload(Report.verification_events),
        )
        .filter(Report.id == report_id)
        .first()
    )
    if report is None:
        raise ReportNotFoundError(str(report_id))
    if report.status != ReportStatus.ANALYZED or report.observation is None:
        raise ReportNotAnalyzedError(str(report_id))

    evidence = get_evidence_for_report(db, report_id)
    return build_fhir_observation(report, evidence)
