"""
Import all models here so `Base.metadata.create_all()` (called from main.py)
discovers every table. Also gives a single import path: `from app.models import Report`.
"""
from app.models.enums import ReportStatus, VerificationStatus
from app.models.user import User
from app.models.location import Location
from app.models.report import Report
from app.models.observation import Observation
from app.models.verification_event import VerificationEvent

__all__ = ["ReportStatus", "VerificationStatus", "User", "Location", "Report", "Observation", "VerificationEvent"]
