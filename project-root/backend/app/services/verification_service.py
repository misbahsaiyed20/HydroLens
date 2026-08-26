"""
Verification is a HUMAN action on top of an already-AI-analyzed report. It
never touches the AI observation itself (Observation row is never written
here) — it only records that a person reviewed it, what they decided, and
updates the report's current verification_status. The full history of that
review process is the audit trail (see VerificationEvent's docstring for
why it's one table, not two).
"""
import uuid

from sqlalchemy.orm import Session

from app.models.enums import ReportStatus, VerificationStatus
from app.models.report import Report
from app.models.verification_event import VerificationEvent
from app.schemas.verification import VerificationEventOut, VerificationHistoryOut, VerificationRequest
from app.services.evidence_fusion_service import ReportNotAnalyzedError, ReportNotFoundError


def _to_history_out(report: Report) -> VerificationHistoryOut:
    events = sorted(report.verification_events, key=lambda e: e.created_at)
    latest = events[-1] if events else None
    return VerificationHistoryOut(
        report_id=report.id,
        verification_status=report.verification_status.value,
        latest_verifier_reference=latest.verifier_reference if latest else None,
        latest_verified_at=latest.created_at if latest else None,
        latest_note=latest.note if latest else None,
        history=[VerificationEventOut.model_validate(e) for e in events],
    )


def submit_verification(
    db: Session, report_id: uuid.UUID, request: VerificationRequest
) -> VerificationHistoryOut:
    """
    Requires the report to have completed AI analysis (mirrors evidence/
    actionability/fhir endpoints' 409 behavior) — verifying a report with
    no AI observation yet to review doesn't make sense. Never modifies
    `report.observation`; only writes a new VerificationEvent row and
    updates `report.verification_status`.
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if report is None:
        raise ReportNotFoundError(str(report_id))
    if report.status != ReportStatus.ANALYZED or report.observation is None:
        raise ReportNotAnalyzedError(str(report_id))

    previous_status = report.verification_status
    new_status = VerificationStatus(request.status)

    event = VerificationEvent(
        report_id=report.id,
        event_type="VERIFICATION",
        previous_status=previous_status,
        new_status=new_status,
        verifier_reference=request.verifier_reference,
        note=request.note,
    )
    db.add(event)
    report.verification_status = new_status
    db.commit()
    db.refresh(report)

    return _to_history_out(report)


def get_verification_history(db: Session, report_id: uuid.UUID) -> VerificationHistoryOut:
    """
    Unlike submit_verification, this does NOT require ANALYZED status —
    viewing an unanalyzed report's verification state is harmless (it will
    just show UNVERIFIED with empty history), so only 404 applies here.
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if report is None:
        raise ReportNotFoundError(str(report_id))

    return _to_history_out(report)
