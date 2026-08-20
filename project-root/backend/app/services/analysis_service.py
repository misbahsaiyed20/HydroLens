"""
Orchestrates AI vision analysis for a single report: moves it through
SUBMITTED -> ANALYZING -> ANALYZED, and writes the resulting indicators into
an Observation row. On failure, reverts to SUBMITTED so it's clear the
report still needs analysis (rather than silently stuck on ANALYZING).

Runs as a FastAPI BackgroundTask (see api/reports.py), so it opens its own
DB session — the request-scoped session from create_report is already
closed by the time this executes.
"""
import logging
import uuid
from pathlib import Path

from app.config import get_settings
from app.database import SessionLocal
from app.models.enums import ReportStatus
from app.models.observation import Observation
from app.models.report import Report
from app.services.vision_service import analyze_image, VisionAnalysisError

logger = logging.getLogger(__name__)
settings = get_settings()


def analyze_report_task(report_id: uuid.UUID) -> None:
    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if report is None:
            logger.warning("analyze_report_task: report %s not found", report_id)
            return

        report.status = ReportStatus.ANALYZING
        db.commit()

        image_path = Path(settings.upload_dir) / report.image_path

        try:
            indicators = analyze_image(image_path)
        except VisionAnalysisError as exc:
            logger.error("Vision analysis failed for report %s: %s", report_id, exc)
            report.status = ReportStatus.SUBMITTED  # revert so it's retriable, not stuck
            db.commit()
            return

        observation = Observation(
            report_id=report.id,
            algae_indicator=indicators.get("algae_indicator"),
            color_anomaly=indicators.get("color_anomaly"),
            visible_waste=indicators.get("visible_waste"),
            turbidity_indicator=indicators.get("turbidity_indicator"),
            image_quality=indicators.get("image_quality"),
            model_confidence=indicators.get("model_confidence"),
        )
        db.add(observation)
        report.status = ReportStatus.ANALYZED
        db.commit()
    finally:
        db.close()
