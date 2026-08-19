import uuid

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.report import Report
from app.models.location import Location
from app.schemas.report import ReportOut, ReportListOut
from app.services.storage_service import save_report_image

router = APIRouter(prefix="/reports", tags=["reports"])


def _report_query(db: Session):
    # Eager-load location + observation so ReportOut never triggers N+1 lazy loads.
    return db.query(Report).options(
        joinedload(Report.location), joinedload(Report.observation)
    )


@router.post("", response_model=ReportOut, status_code=201)
async def create_report(
    latitude: float = Form(..., ge=-90, le=90),
    longitude: float = Form(..., ge=-180, le=180),
    stream_name: str | None = Form(default=None),
    stream_segment: str | None = Form(default=None),
    description: str | None = Form(default=None, max_length=2000),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Citizen submits a stream observation: photo + coordinates + optional
    description. This is intentionally the ONLY write path in Sprint 1 —
    no AI analysis, no evidence fusion, no case creation yet. Those hang off
    this same Report row in later sprints.
    """
    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    stored_filename = save_report_image(image, contents)

    location = Location(
        latitude=latitude,
        longitude=longitude,
        stream_name=(stream_name or None),
        stream_segment=(stream_segment or None),
    )
    db.add(location)
    db.flush()  # get location.id without a full commit yet

    report = Report(
        location_id=location.id,
        image_path=stored_filename,
        description=(description or None),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return _report_query(db).filter(Report.id == report.id).first()


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: uuid.UUID, db: Session = Depends(get_db)):
    report = _report_query(db).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


@router.get("", response_model=ReportListOut)
def list_reports(
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    total = db.query(Report).count()
    items = (
        _report_query(db)
        .order_by(Report.submitted_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return ReportListOut(total=total, items=items)
