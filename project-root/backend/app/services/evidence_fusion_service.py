"""
Ties related-report detection, baseline estimation, and confidence scoring
into a single explainable EvidenceFusionResult for one report.

Scientific boundary: outputs describe "environmental anomaly confidence" /
observable conditions, never a diagnosis or outbreak prediction. The only
recommended action is human officer verification or continued monitoring —
this service makes no automatic public-health decision.
"""
import uuid

from sqlalchemy.orm import Session, joinedload

from app.models.enums import ReportStatus
from app.models.report import Report
from app.schemas.evidence import EvidenceFusionResult, RelatedObservationSummary
from app.services.baseline_service import get_location_baseline
from app.services.confidence_service import calculate_confidence, is_abnormal
from app.services.indicator_scales import get_indicator_severity
from app.services.related_report_service import RelatedReport, find_related_reports


class ReportNotFoundError(Exception):
    pass


class ReportNotAnalyzedError(Exception):
    pass


def _summarize(related: RelatedReport) -> RelatedObservationSummary:
    obs = related.report.observation
    return RelatedObservationSummary(
        report_id=related.report.id,
        distance_meters=round(related.distance_meters, 1),
        minutes_apart=round(related.minutes_apart, 1),
        algae_indicator=obs.algae_indicator if obs else None,
        color_anomaly=obs.color_anomaly if obs else None,
        turbidity_indicator=obs.turbidity_indicator if obs else None,
        visible_waste=obs.visible_waste if obs else None,
        image_quality=obs.image_quality if obs else None,
    )


def get_evidence_for_report(db: Session, report_id: uuid.UUID) -> EvidenceFusionResult:
    report = (
        db.query(Report)
        .options(joinedload(Report.location), joinedload(Report.observation))
        .filter(Report.id == report_id)
        .first()
    )
    if report is None:
        raise ReportNotFoundError(str(report_id))

    if report.status != ReportStatus.ANALYZED or report.observation is None:
        raise ReportNotAnalyzedError(str(report_id))

    related = find_related_reports(db, report)
    baseline = get_location_baseline(db, report)
    confidence = calculate_confidence(report, related, baseline)

    eval_abnormal = is_abnormal(report.observation)
    if not eval_abnormal:
        condition_summary = "Observation does not indicate an environmental anomaly."
    elif confidence.level == "HIGH":
        condition_summary = (
            f"Elevated environmental anomaly confidence, corroborated by "
            f"{len(confidence.supporting)} nearby report(s)."
        )
    elif confidence.level == "MODERATE":
        condition_summary = "Possible environmental anomaly indicated; evidence is moderate."
    else:
        condition_summary = "Possible environmental anomaly observed, but corroborating evidence is limited."

    if eval_abnormal and confidence.level in ("HIGH", "MODERATE"):
        recommended_action = "Officer verification recommended."
    else:
        recommended_action = "Continue monitoring — evidence does not yet meet the officer-escalation threshold."

    return EvidenceFusionResult(
        report_id=report.id,
        confidence_score=round(confidence.score, 3),
        confidence_level=confidence.level,
        indicator_severity=get_indicator_severity(report.observation),
        condition_summary=condition_summary,
        related_report_count=len(related),
        supporting_observations=[_summarize(r) for r in confidence.supporting],
        conflicting_observations=[_summarize(r) for r in confidence.conflicting],
        baseline=baseline,
        evidence_reasons=confidence.reasons,
        recommended_action=recommended_action,
    )
