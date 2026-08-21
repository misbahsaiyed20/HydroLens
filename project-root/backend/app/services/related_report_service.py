"""
Finds candidate reports that may refer to the same environmental event as a
given report, using the two "hard gate" signals from the Sprint 3 spec:
geographic proximity and temporal proximity (both configurable — see
config.py). stream_name match is surfaced as informational metadata only
(`same_stream_name`) rather than folded into the gate or the score — the
spec explicitly says not to require it, and citizen reports frequently
omit it. Whether/how strongly it should influence scoring is left as a
documented Sprint 3 limitation rather than an ad-hoc bonus term (see
README).

These are RELATED CANDIDATES, not confirmed duplicates of the same event —
confidence_service decides how strongly they corroborate one another.
"""
from datetime import timedelta
from typing import NamedTuple

from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.models.enums import ReportStatus
from app.models.report import Report
from app.services.geo_utils import haversine_meters
from app.services.time_utils import to_naive_utc

settings = get_settings()


class RelatedReport(NamedTuple):
    report: Report
    distance_meters: float
    minutes_apart: float
    same_stream_name: bool


def find_related_reports(db: Session, report: Report) -> list[RelatedReport]:
    """
    Only ANALYZED reports (i.e. with a populated Observation) are eligible —
    evidence fusion needs indicators to compare, and a report still
    SUBMITTED/ANALYZING has none yet.
    """
    if report.location is None:
        return []

    window = timedelta(minutes=settings.related_report_time_window_minutes)
    report_time = to_naive_utc(report.submitted_at)
    earliest, latest = report_time - window, report_time + window

    candidates = (
        db.query(Report)
        .options(joinedload(Report.location), joinedload(Report.observation))
        .filter(Report.id != report.id)
        .filter(Report.status == ReportStatus.ANALYZED)
        .filter(Report.submitted_at >= earliest, Report.submitted_at <= latest)
        .all()
    )

    related: list[RelatedReport] = []
    for candidate in candidates:
        if candidate.location is None or candidate.observation is None:
            continue

        distance = haversine_meters(
            report.location.latitude, report.location.longitude,
            candidate.location.latitude, candidate.location.longitude,
        )
        if distance > settings.related_report_radius_meters:
            continue

        minutes_apart = abs((to_naive_utc(candidate.submitted_at) - report_time).total_seconds()) / 60
        same_stream = bool(
            report.location.stream_name
            and candidate.location.stream_name
            and report.location.stream_name.strip().lower()
            == candidate.location.stream_name.strip().lower()
        )
        related.append(RelatedReport(candidate, distance, minutes_apart, same_stream))

    return related
