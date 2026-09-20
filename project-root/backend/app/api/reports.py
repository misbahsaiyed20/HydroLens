import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user, require_reviewer
from app.database import get_db
from app.models.enums import ReportStatus, UserRole
from app.models.location import Location
from app.models.report import Report
from app.models.user import User
from app.schemas.actionability import ActionabilityResult
from app.schemas.evidence import EvidenceFusionResult
from app.schemas.explore import ExploreListOut, ExploreObservationOut
from app.schemas.report import ReportListOut, ReportOut
from app.schemas.verification import VerificationHistoryOut, VerificationRequest
from app.services.actionability_service import get_actionability_for_report
from app.services.analysis_service import analyze_report_task
from app.services.evidence_fusion_service import ReportNotAnalyzedError, ReportNotFoundError, get_evidence_for_report
from app.services.fhir_service import get_fhir_observation_for_report
from app.services.storage_service import save_report_image
from app.services.verification_service import get_verification_history, submit_verification

router = APIRouter(prefix="/reports", tags=["reports"])
logger = logging.getLogger("aqua_sentinel")


def _report_query(db: Session):
    return db.query(Report).options(joinedload(Report.location), joinedload(Report.observation))


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
    base = (
        _report_query(db)
        .join(Report.observation)
        .filter(Report.status == ReportStatus.ANALYZED)
    )
    total = base.count()
    reports = base.order_by(Report.submitted_at.desc()).offset(offset).limit(limit).all()

    return ExploreListOut(
        total=total,
        items=[
            ExploreObservationOut(
                id=report.id,
                stream_name=report.location.stream_name,
                image_path=report.image_path,
                condition_summary=_public_condition_summary(report),
                turbidity_indicator=report.observation.turbidity_indicator if report.observation else None,
                algae_indicator=report.observation.algae_indicator if report.observation else None,
                visible_waste=report.observation.visible_waste if report.observation else None,
                color_anomaly=report.observation.color_anomaly if report.observation else None,
                image_quality=report.observation.image_quality if report.observation else None,
                verification_status=report.verification_status.value,
                submitted_at=report.submitted_at,
            )
            for report in reports
        ],
    )


@router.get("/explore/{report_id}", response_model=ExploreObservationOut)
def explore_report_detail(report_id: uuid.UUID, db: Session = Depends(get_db)):
    report = (
        _report_query(db)
        .join(Report.observation)
        .filter(Report.id == report_id, Report.status == ReportStatus.ANALYZED)
        .first()
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Public observation not found.")

    return ExploreObservationOut(
        id=report.id,
        stream_name=report.location.stream_name,
        image_path=report.image_path,
        condition_summary=_public_condition_summary(report),
        turbidity_indicator=report.observation.turbidity_indicator if report.observation else None,
        algae_indicator=report.observation.algae_indicator if report.observation else None,
        visible_waste=report.observation.visible_waste if report.observation else None,
        color_anomaly=report.observation.color_anomaly if report.observation else None,
        image_quality=report.observation.image_quality if report.observation else None,
        verification_status=report.verification_status.value,
        submitted_at=report.submitted_at,
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
    db.flush()

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
    base = _report_query(db).filter(Report.user_id == current_user.id)
    total = base.count()
    items = base.order_by(Report.submitted_at.desc()).offset(offset).limit(limit).all()
    return ReportListOut(total=total, items=items)


@router.get("", response_model=ReportListOut)
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
    status: ReportStatus | None = Query(default=None),
    verification_status: str | None = Query(default=None, pattern="^(UNVERIFIED|VERIFIED|REJECTED)$"),
    search: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    query = _report_query(db)
    if status is not None:
        query = query.filter(Report.status == status)
    if verification_status is not None:
        query = query.filter(Report.verification_status == verification_status)

    reports = query.order_by(Report.submitted_at.desc()).all()
    needle = (search or "").strip().lower()
    if needle:
        reports = [
            report
            for report in reports
            if needle in str(report.id).lower()
            or needle in (report.location.stream_name or "").lower()
            or needle in (report.location.stream_segment or "").lower()
        ]

    total = len(reports)
    return ReportListOut(total=total, items=reports[offset: offset + limit])


@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = _report_query(db).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    if current_user.role != UserRole.REVIEWER and report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this report.")
    return report


@router.get("/{report_id}/evidence", response_model=EvidenceFusionResult)
def get_report_evidence(report_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_reviewer)):
    try:
        return get_evidence_for_report(db, report_id)
    except ReportNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found.")
    except ReportNotAnalyzedError:
        raise HTTPException(status_code=409, detail="Report has not completed AI analysis yet.")


@router.get("/{report_id}/actionability", response_model=ActionabilityResult)
def get_report_actionability(report_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_reviewer)):
    try:
        return get_actionability_for_report(db, report_id)
    except ReportNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found.")
    except ReportNotAnalyzedError:
        raise HTTPException(status_code=409, detail="Report has not completed AI analysis yet.")


@router.get("/{report_id}/fhir")
def get_report_fhir(report_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_reviewer)) -> dict:
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
    try:
        request.verifier_reference = current_user.email or current_user.display_name or str(current_user.id)
        result = submit_verification(db, report_id, request)
        logger.info("report %s verification -> %s", report_id, result.verification_status)
        return result
    except ReportNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found.")
    except ReportNotAnalyzedError:
        raise HTTPException(status_code=409, detail="Report has not completed AI analysis yet.")


@router.get("/{report_id}/verification", response_model=VerificationHistoryOut)
def get_report_verification(report_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_reviewer)):
    try:
        return get_verification_history(db, report_id)
    except ReportNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found.")
