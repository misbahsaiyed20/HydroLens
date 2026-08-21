"""
Helpers for building Location/Report/Observation rows directly in a test DB
session — Sprint 3's evidence-fusion tests need many ANALYZED reports with
specific coordinates/timestamps/indicators, which would be slow and noisy
to create via the real upload API + mocked Gemini responses each time.
"""
from datetime import datetime, timedelta, timezone

from app.models.enums import ReportStatus
from app.models.location import Location
from app.models.observation import Observation
from app.models.report import Report

BASE_LAT, BASE_LON = 23.0225, 72.5714  # Sabarmati riverfront, Ahmedabad


def make_analyzed_report(
    db,
    *,
    lat: float = BASE_LAT,
    lon: float = BASE_LON,
    minutes_ago: float = 10,
    stream_name: str | None = None,
    algae_indicator: str | None = "none",
    color_anomaly: str | None = "none",
    visible_waste: bool | None = False,
    turbidity_indicator: str | None = "clear",
    image_quality: str | None = "good",
    model_confidence: float | None = 0.9,
    status: ReportStatus = ReportStatus.ANALYZED,
) -> Report:
    location = Location(latitude=lat, longitude=lon, stream_name=stream_name)
    db.add(location)
    db.flush()

    submitted_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=minutes_ago)
    report = Report(
        location_id=location.id,
        image_path="test.png",
        status=status,
        submitted_at=submitted_at,
        updated_at=submitted_at,
    )
    db.add(report)
    db.flush()

    if status == ReportStatus.ANALYZED:
        observation = Observation(
            report_id=report.id,
            algae_indicator=algae_indicator,
            color_anomaly=color_anomaly,
            visible_waste=visible_waste,
            turbidity_indicator=turbidity_indicator,
            image_quality=image_quality,
            model_confidence=model_confidence,
        )
        db.add(observation)

    db.commit()
    db.refresh(report)
    return report
