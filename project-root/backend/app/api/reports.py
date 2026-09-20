import uuid
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user, require_reviewer
from app.database import get_db
from app.models.enums import ReportStatus, UserRole
from app.models.report import Report
from app.models.location import Location
from app.models.user import User
from app.schemas.report import ReportOut, ReportListOut
from app.schemas.explore import ExploreListOut, ExploreObservationOut
from app.schemas.evidence import EvidenceFusionResult
from app.schemas.actionability import ActionabilityResult
from app.services.storage_service import save_report_image
from app.services.analysis_service import analyze_report_task
from app.services.evidence_fusion_service import (
    ReportNotAnalyzedError,
    ReportNotFoundError,
    get_evidence_for_report,
)
from app.services.actionability_service import get_actionability_for_report
from app.services.fhir_service import get_fhir_observation_for_report
from app.schemas.verification import VerificationRequest, VerificationHistoryOut
from app.services.verification_service import get_verification_history, submit_verification

router = APIRouter(prefix="/reports", tags=["reports"])
logger = logging.getLogger("aqua_sentinel")



def _public_condition_summary(report: Report) -> str:
    observation = report.observation
    if observation is None:
        return "Awaiting AI analysis."
    parts: list[str] = []
    if observation.turbidity_indicator and observation.turbidity_indicator not in {"clear", "none"}:
        parts.append(f"turbidity appears {observation.turbidity_indicator}")
    if observation.algae_indicator and observation.algae_indicator != "none":
        parts.append(f"algae indicator: {observation.algae_indicator}")
    if observation.visible_waste:
        parts.append("visible waste detected")
    if observation.color_anomaly and observation.color_anomaly != "none":
        parts.append(f"color anomaly: {observation.color_anomaly}")
    if not parts:
        return "No obvious visual anomaly recorded."
    return "HydroLens detected " + ", ".join(parts) + "."


@router.get("/explore", response_model=ExploreListOut)
def explore_reports(
    db: Session = Depends(get_db),
    limit: int = Query(default=24, ge=1, le=60),
    offset: int = Query(default=0, ge=0),
):
    """
    Public, anonymized community view.

    Only ANALYZED reports are exposed. Private user identity, descriptions,
    exact coordinates, evidence-fusion details, and reviewer notes are omitted.
    """
    base = (
        _report_query(db)
        .join(Report.observation)
        .filter(Report.status == ReportStatus.ANALYZED)
    )
    total = base.count()
    reports = (
        base.order_by(Report.submitted_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    items = [
        ExploreObservationOut(
            id=report.id,
            stream_name=report.location.stream_name,
            image_path=report.image_path,
            condition_summary=_public_condition_summary(report),
            turbidity_indicator=report.observation.turbidity_indicator if report.observation else None,
            algae_indicator=report.observation.algae_indicator if report.observation else None,
            visible_waste=report.observation.visible_waste if report.observation else None,
            verification_status=report.verification_status.value,
            submitted_at=report.submitted_at,
        )
        for report in reports
    ]
    return ExploreListOut(total=total, items=items)


def _report_query(db: Session):
    # Eager-load location + observation so ReportOut never triggers N+1 lazy loads.
    return db.query(Report).options(
        joinedload(Report.location), joinedload(Report.observation)
    )


@router.post("", response_model=ReportOut, status_code=201)
async def create_report(
    background_tasks: BackgroundTasks,
    latitude: float = Form(..., ge=-90, le=90),
    longitude: float = Form(..., ge=-180, le=180),
    stream_name: str | None = Form(default=None),
    stream_segment: str | None = Form(default=None),
    description: str | None = Form(default=None, max_length=2000),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Citizen (or reviewer) submits a stream observation: photo + coordinates
    + optional description. Requires authentication — the report is
    attributed to the submitting user via `user_id`. The report is created
    and returned as SUBMITTED immediately; AI vision analysis (Sprint 2)
    then runs in the background and moves it through ANALYZING -> ANALYZED,
    populating Observation. Evidence fusion and case creation still come in
    later sprints.

    Note: `user_id` is nullable on the Report model and pre-auth rows exist
    with it unset — this endpoint now always sets it, but nothing here
    touches or reinterprets those older anonymous rows.
    """
    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    stored_filename = save_report_image(image, contents)

    location = Location(
        latitude=latitude,
        longitude=longitude,
        stream_name=(stream_name or None),
        stream_segment=(stream_segment or None),
    )
    db.add(location)
    db.flush()  # get location.id without a full commit yet

    report = Report(
        user_id=current_user.id,
        location_id=location.id,
        image_path=stored_filename,
        description=(description or None),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    logger.info("report created: id=%s location=(%.4f,%.4f)", report.id, latitude, longitude)

    background_tasks.add_task(analyze_report_task, report.id)

    return _report_query(db).filter(Report.id == report.id).first()


@router.get("/me", response_model=ReportListOut)
def list_my_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Citizen's (or reviewer's) own submission history."""
    base = _report_query(db).filter(Report.user_id == current_user.id)
    total = base.count()
    items = base.order_by(Report.submitted_at.desc()).offset(offset).limit(limit).all()
    return ReportListOut(total=total, items=items)


@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = _report_query(db).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    # A citizen may only view their own report/status; a reviewer may view any.
    if current_user.role != UserRole.REVIEWER and report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this report.")
    return report


@router.get("", response_model=ReportListOut)
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Reviewer-only: full report list across all citizens. Citizens use GET /reports/me instead."""
    total = db.query(Report).count()
    items = (
        _report_query(db)
        .order_by(Report.submitted_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return ReportListOut(total=total, items=items)


@router.get("/{report_id}/evidence", response_model=EvidenceFusionResult)
def get_report_evidence(
    report_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_reviewer)
):
    """
    Sprint 3: fuses related reports + location baseline into an explainable
    confidence assessment for this report. 404 if the report doesn't exist;
    409 if it hasn't finished AI analysis yet (nothing to fuse evidence
    from). A report with zero related reports and no baseline is NOT an
    error — it just comes back with LOW confidence and an explanatory
    reason, since insufficient evidence is a valid outcome, not a failure.
    """
    try:
        return get_evidence_for_report(db, report_id)
    except ReportNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found.")
    except ReportNotAnalyzedError:
        raise HTTPException(status_code=409, detail="Report has not completed AI analysis yet.")


@router.get("/{report_id}/actionability", response_model=ActionabilityResult)
def get_report_actionability(
    report_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_reviewer)
):
    """
    Sprint 4: converts the existing evidence-fusion result into an
    operational review recommendation (CONTINUE_MONITORING /
    REVIEW_RECOMMENDED / PRIORITY_REVIEW) plus an exposure-risk signal
    (LOW / MODERATE / ELEVATED). Never a diagnosis — see
    actionability_service.py and exposure_risk_service.py docstrings for
    the scientific-safety framing. Same 404/409 semantics as /evidence.
    """
    try:
        return get_actionability_for_report(db, report_id)
    except ReportNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found.")
    except ReportNotAnalyzedError:
        raise HTTPException(status_code=409, detail="Report has not completed AI analysis yet.")


@router.get("/{report_id}/fhir")
def get_report_fhir(
    report_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_reviewer)
) -> dict:
    """
    Sprint 4: FHIR-compatible Observation resource for this report (see
    fhir_service.py). No response_model is declared — FHIR resources are
    heterogeneous by design (component lists vary per report), and forcing
    a rigid Pydantic schema here would mean either an incomplete mapping or
    pulling in a full FHIR resource library, neither of which this sprint
    calls for. Same 404/409 semantics as /evidence and /actionability.
    """
    try:
        return get_fhir_observation_for_report(db, report_id)
    except ReportNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found.")
    except ReportNotAnalyzedError:
        raise HTTPException(status_code=409, detail="Report has not completed AI analysis yet.")


@router.post("/{report_id}/verify", response_model=VerificationHistoryOut)
def verify_report(
    report_id: uuid.UUID,
    request: VerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
):
    """
    Sprint 5: records a HUMAN verification decision (VERIFIED or REJECTED)
    for an already-analyzed report. Never modifies the AI-generated
    Observation — only writes a new audit event and updates
    `report.verification_status`. 404 if the report doesn't exist, 409 if
    it hasn't finished AI analysis (nothing to verify yet), 422
    automatically for an invalid `status` value (e.g. "UNVERIFIED", which
    isn't a valid target for this action — see VerificationRequest).
    """
    try:
        # verifier_reference always reflects the authenticated reviewer,
        # never a client-supplied string (see VerificationRequest
        # docstring) — this also fixes a real gap where the frontend
        # never sent this now-required-by-convention identity field at
        # all, which would otherwise 422 on every verify/reject attempt.
        request.verifier_reference = current_user.email or current_user.display_name or str(current_user.id)
        result = submit_verification(db, report_id, request)
        # Verifier reference/note are user-supplied free text and are NOT
        # logged verbatim (Phase 5: no unnecessary personal data in logs)
        # — only the status transition and report id.
        logger.info("report %s verification -> %s", report_id, result.verification_status)
        return result
    except ReportNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found.")
    except ReportNotAnalyzedError:
        raise HTTPException(status_code=409, detail="Report has not completed AI analysis yet.")


@router.get("/{report_id}/verification", response_model=VerificationHistoryOut)
def get_report_verification(
    report_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_reviewer)
):
    """
    Sprint 5: current verification state + full audit history for this
    report. Unlike POST /verify, this does NOT require ANALYZED status —
    viewing an unanalyzed report's (default UNVERIFIED, empty-history)
    state is harmless. Only 404 applies here.
    """
    try:
        return get_verification_history(db, report_id)
    except ReportNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found.")
