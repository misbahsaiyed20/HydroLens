"""
A "case" is an ANALYZED report viewed through its evidence-fusion +
actionability + verification results — there is no separate Case DB table
(Phase 11: only add a new model if genuinely required; the existing
Report/Observation/VerificationEvent tables already carry everything a
case view needs). Filtering by confidence/exposure/action level requires
computing evidence for each analyzed report — same O(n) caveat as
dashboard_service.py, acceptable at this project's scale.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.enums import ReportStatus
from app.models.report import Report
from app.schemas.case import CaseDetail, CaseListResult, CaseSummary
from app.schemas.verification import VerificationEventOut
from app.services.actionability_service import build_actionability_result
from app.services.evidence_fusion_service import (
    ReportNotAnalyzedError,
    ReportNotFoundError,
    get_evidence_for_report,
)


def _to_summary(report, evidence, action) -> CaseSummary:
    return CaseSummary(
        report_id=report.id,
        location=report.location,
        condition_summary=evidence.condition_summary,
        confidence_score=evidence.confidence_score,
        confidence_level=evidence.confidence_level,
        exposure_risk_level=action.exposure_risk_level,
        action_level=action.action_level,
        verification_status=report.verification_status.value,
        supporting_count=len(evidence.supporting_observations),
        conflicting_count=len(evidence.conflicting_observations),
        created_at=report.submitted_at,
        updated_at=report.updated_at,
    )


def list_cases(
    db: Session,
    *,
    confidence_level: Optional[str] = None,
    exposure_risk_level: Optional[str] = None,
    action_level: Optional[str] = None,
    verification_status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius_meters: Optional[float] = None,
    limit: int = 20,
    offset: int = 0,
) -> CaseListResult:
    query = (
        db.query(Report)
        .options(joinedload(Report.location), joinedload(Report.observation))
        .filter(Report.status == ReportStatus.ANALYZED)
    )
    if verification_status:
        query = query.filter(Report.verification_status == verification_status)
    if date_from:
        query = query.filter(Report.submitted_at >= date_from)
    if date_to:
        query = query.filter(Report.submitted_at <= date_to)

    reports = query.order_by(Report.submitted_at.desc()).all()

    if lat is not None and lon is not None and radius_meters is not None:
        from app.services.geo_utils import haversine_meters
        reports = [
            r for r in reports
            if r.location is not None
            and haversine_meters(lat, lon, r.location.latitude, r.location.longitude) <= radius_meters
        ]

    matched: list[CaseSummary] = []
    for report in reports:
        evidence = get_evidence_for_report(db, report.id)
        if confidence_level and evidence.confidence_level != confidence_level:
            continue
        action = build_actionability_result(evidence)
        if exposure_risk_level and action.exposure_risk_level != exposure_risk_level:
            continue
        if action_level and action.action_level != action_level:
            continue
        matched.append(_to_summary(report, evidence, action))

    total = len(matched)
    page = matched[offset: offset + limit]
    return CaseListResult(total=total, items=page)


def get_case_detail(db: Session, report_id: uuid.UUID) -> CaseDetail:
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
    action = build_actionability_result(evidence)
    history = sorted(report.verification_events, key=lambda e: e.created_at)

    return CaseDetail(
        report_id=report.id,
        status=report.status.value,
        verification_status=report.verification_status.value,
        location=report.location,
        observation=report.observation,
        description=report.description,
        created_at=report.submitted_at,
        updated_at=report.updated_at,
        condition_summary=evidence.condition_summary,
        confidence_score=evidence.confidence_score,
        confidence_level=evidence.confidence_level,
        indicator_severity=evidence.indicator_severity,
        exposure_risk_level=action.exposure_risk_level,
        action_level=action.action_level,
        recommended_action=action.recommended_action,
        supporting_observations=evidence.supporting_observations,
        conflicting_observations=evidence.conflicting_observations,
        evidence_reasons=evidence.evidence_reasons,
        baseline=evidence.baseline,
        verification_history=[VerificationEventOut.model_validate(e) for e in history],
        fhir_url=f"/api/reports/{report.id}/fhir",
    )
