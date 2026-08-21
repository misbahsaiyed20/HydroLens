"""
Estimates the "normal" environmental condition for a report's location from
historical ANALYZED observations — a simple mode/frequency baseline, not a
statistical model, per the Sprint 3 spec's "do not over-engineer" guidance.

IMPORTANT — avoiding circularity: baseline candidates must be OLDER than
the current related-report time window (report.submitted_at minus
RELATED_REPORT_TIME_WINDOW_MINUTES). If the baseline instead included the
very reports being scored as current evidence, a strongly corroborated
event would just recalibrate "normal" to match itself and never show up as
a deviation. So "historical" here means "outside the current event
window", not merely "created before this exact report".

Explicitly distinguishes two states that the spec calls out as important
to keep separate:
  - available=False: too little historical data to say what's normal
  - available=True, deviates=False: baseline exists, current observation
    matches it
Absence of history is never silently treated as an anomaly.
"""
from collections import Counter
from datetime import timedelta

from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.models.enums import ReportStatus
from app.models.report import Report
from app.schemas.evidence import BaselineSummary
from app.services.geo_utils import haversine_meters
from app.services.indicator_scales import ALGAE_SEVERITY, TURBIDITY_SEVERITY
from app.services.time_utils import to_naive_utc

settings = get_settings()


def _mode(values: list[str]) -> str | None:
    """Most frequent value. Ties broken toward the LOWER-severity option so
    an ambiguous historical mix never overstates a deviation."""
    if not values:
        return None
    counts = Counter(values)
    top = max(counts.values())
    tied = [v for v, c in counts.items() if c == top]
    return min(tied, key=lambda v: TURBIDITY_SEVERITY.get(v, ALGAE_SEVERITY.get(v, 0)))


def get_location_baseline(db: Session, report: Report) -> BaselineSummary:
    if report.location is None:
        return BaselineSummary(available=False, historical_observation_count=0)

    report_time = to_naive_utc(report.submitted_at)
    cutoff = report_time - timedelta(minutes=settings.related_report_time_window_minutes)

    candidates = (
        db.query(Report)
        .options(joinedload(Report.location), joinedload(Report.observation))
        .filter(Report.id != report.id)
        .filter(Report.status == ReportStatus.ANALYZED)
        .filter(Report.submitted_at < cutoff)
        .all()
    )

    historical = []
    for candidate in candidates:
        if candidate.location is None or candidate.observation is None:
            continue
        distance = haversine_meters(
            report.location.latitude, report.location.longitude,
            candidate.location.latitude, candidate.location.longitude,
        )
        if distance <= settings.related_report_radius_meters:
            historical.append(candidate.observation)

    count = len(historical)
    if count < settings.baseline_minimum_observations:
        return BaselineSummary(available=False, historical_observation_count=count)

    turbidity_values = [o.turbidity_indicator for o in historical if o.turbidity_indicator in TURBIDITY_SEVERITY]
    algae_values = [o.algae_indicator for o in historical if o.algae_indicator in ALGAE_SEVERITY]
    waste_flags = [o.visible_waste for o in historical if o.visible_waste is not None]

    turbidity_baseline = _mode(turbidity_values)
    algae_baseline = _mode(algae_values)
    waste_rate = (sum(1 for w in waste_flags if w) / len(waste_flags)) if waste_flags else None

    current = report.observation
    deviates = False
    if current is not None:
        if turbidity_baseline and current.turbidity_indicator in TURBIDITY_SEVERITY:
            if TURBIDITY_SEVERITY[current.turbidity_indicator] > TURBIDITY_SEVERITY[turbidity_baseline]:
                deviates = True
        if algae_baseline and current.algae_indicator in ALGAE_SEVERITY:
            if ALGAE_SEVERITY[current.algae_indicator] > ALGAE_SEVERITY[algae_baseline]:
                deviates = True
        if waste_rate is not None and current.visible_waste and waste_rate < 0.2:
            deviates = True

    return BaselineSummary(
        available=True,
        historical_observation_count=count,
        turbidity_baseline=turbidity_baseline,
        algae_baseline=algae_baseline,
        waste_rate=waste_rate,
        deviates=deviates,
    )
