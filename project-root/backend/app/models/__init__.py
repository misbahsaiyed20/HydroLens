"""
Import all models here so `Base.metadata.create_all()` (called from main.py)
discovers every table. Also gives a single import path: `from app.models import Report`.
"""
from app.models.enums import ReportStatus
from app.models.user import User
from app.models.location import Location
from app.models.report import Report
from app.models.observation import Observation

__all__ = ["ReportStatus", "User", "Location", "Report", "Observation"]
