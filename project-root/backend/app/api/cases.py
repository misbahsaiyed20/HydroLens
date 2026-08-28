import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.case import CaseDetail, CaseListResult
from app.services.case_service import get_case_detail, list_cases
from app.services.evidence_fusion_service import ReportNotAnalyzedError, ReportNotFoundError

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("", response_model=CaseListResult)
def get_cases(
    db: Session = Depends(get_db),
    confidence_level: Optional[str] = Query(default=None, pattern="^(LOW|MODERATE|HIGH)$"),
    exposure_risk_level: Optional[str] = Query(default=None, pattern="^(LOW|MODERATE|ELEVATED)$"),
    action_level: Optional[str] = Query(default=None, pattern="^(CONTINUE_MONITORING|REVIEW_RECOMMENDED|PRIORITY_REVIEW)$"),
    verification_status: Optional[str] = Query(default=None, pattern="^(UNVERIFIED|VERIFIED|REJECTED)$"),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius_meters: Optional[float] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """A "case" is an ANALYZED report — see case_service.py docstring for
    why there's no separate Case table. Search by report ID: use
    GET /api/cases/{id} directly rather than a query param here."""
    return list_cases(
        db,
        confidence_level=confidence_level,
        exposure_risk_level=exposure_risk_level,
        action_level=action_level,
        verification_status=verification_status,
        date_from=date_from,
        date_to=date_to,
        lat=lat,
        lon=lon,
        radius_meters=radius_meters,
        limit=limit,
        offset=offset,
    )


@router.get("/{report_id}", response_model=CaseDetail)
def get_case(report_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return get_case_detail(db, report_id)
    except ReportNotFoundError:
        raise HTTPException(status_code=404, detail="Case not found.")
    except ReportNotAnalyzedError:
        raise HTTPException(status_code=409, detail="Report has not completed AI analysis yet — not yet a case.")
