"""
Aggregates counts for the dashboard from live DB data. Reuses
evidence_fusion_service + actionability_service.build_actionability_result
(the pure function, not the DB-hitting wrapper) to avoid recomputing
evidence twice per report. No caching yet — see README limitations: at
larger report volumes this becomes an O(n) evidence-fusion scan on every
dashboard load.
"""
from sqlalchemy.orm import Session

from app.models.enums import ReportStatus, VerificationStatus
from app.models.report import Report
from app.schemas.dashboard import DashboardSummary
from app.services.actionability_service import build_actionability_result
from app.services.evidence_fusion_service import get_evidence_for_report


def get_dashboard_summary(db: Session) -> DashboardSummary:
    total_reports = db.query(Report).count()
    pending_review = (
        db.query(Report)
        .filter(Report.status.in_([ReportStatus.SUBMITTED, ReportStatus.ANALYZING]))
        .count()
    )
    analyzed_reports = db.query(Report).filter(Report.status == ReportStatus.ANALYZED).count()
    verified_cases = db.query(Report).filter(Report.verification_status == VerificationStatus.VERIFIED).count()
    rejected_cases = db.query(Report).filter(Report.verification_status == VerificationStatus.REJECTED).count()

    high_confidence_cases = 0
    cases_requiring_review = 0

    analyzed_ids = [r.id for r in db.query(Report.id).filter(Report.status == ReportStatus.ANALYZED).all()]
    for report_id in analyzed_ids:
        evidence = get_evidence_for_report(db, report_id)
        if evidence.confidence_level == "HIGH":
            high_confidence_cases += 1
        action = build_actionability_result(evidence)
        if action.action_level in ("REVIEW_RECOMMENDED", "PRIORITY_REVIEW"):
            cases_requiring_review += 1

    return DashboardSummary(
        total_reports=total_reports,
        pending_review=pending_review,
        analyzed_reports=analyzed_reports,
        high_confidence_cases=high_confidence_cases,
        verified_cases=verified_cases,
        rejected_cases=rejected_cases,
        cases_requiring_review=cases_requiring_review,
    )
