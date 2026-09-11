from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_reviewer
from app.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import get_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(require_reviewer)):
    return get_dashboard_summary(db)
