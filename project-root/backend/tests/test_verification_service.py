import uuid

import pytest

from app.models.enums import ReportStatus, VerificationStatus
from app.schemas.verification import VerificationRequest
from app.services.evidence_fusion_service import ReportNotAnalyzedError, ReportNotFoundError
from app.services.verification_service import get_verification_history, submit_verification
from tests.factories import make_analyzed_report


def test_new_report_starts_unverified(db_session):
    report = make_analyzed_report(db_session)
    assert report.verification_status == VerificationStatus.UNVERIFIED

    history = get_verification_history(db_session, report.id)
    assert history.verification_status == "UNVERIFIED"
    assert history.history == []


def test_analyzed_report_can_be_verified(db_session):
    report = make_analyzed_report(db_session)
    result = submit_verification(
        db_session, report.id, VerificationRequest(status="VERIFIED", verifier_reference="reviewer_1")
    )
    assert result.verification_status == "VERIFIED"
    assert result.latest_verifier_reference == "reviewer_1"
    assert len(result.history) == 1
    assert result.history[0].previous_status == "UNVERIFIED"
    assert result.history[0].new_status == "VERIFIED"


def test_analyzed_report_can_be_rejected(db_session):
    report = make_analyzed_report(db_session)
    result = submit_verification(
        db_session, report.id, VerificationRequest(status="REJECTED", verifier_reference="reviewer_2", note="blurry, inconclusive")
    )
    assert result.verification_status == "REJECTED"
    assert result.latest_note == "blurry, inconclusive"


def test_nonexistent_report_raises_not_found(db_session):
    with pytest.raises(ReportNotFoundError):
        submit_verification(
            db_session, uuid.uuid4(), VerificationRequest(status="VERIFIED", verifier_reference="x")
        )


def test_unanalyzed_report_raises_not_analyzed(db_session):
    report = make_analyzed_report(db_session, status=ReportStatus.SUBMITTED)
    with pytest.raises(ReportNotAnalyzedError):
        submit_verification(
            db_session, report.id, VerificationRequest(status="VERIFIED", verifier_reference="x")
        )


def test_verification_does_not_overwrite_ai_observation(db_session):
    report = make_analyzed_report(db_session, algae_indicator="high", model_confidence=0.95)
    original_confidence = report.observation.model_confidence
    original_algae = report.observation.algae_indicator

    submit_verification(
        db_session, report.id, VerificationRequest(status="VERIFIED", verifier_reference="reviewer_1")
    )

    db_session.refresh(report)
    assert report.observation.model_confidence == original_confidence
    assert report.observation.algae_indicator == original_algae


def test_second_verification_records_previous_status(db_session):
    report = make_analyzed_report(db_session)
    submit_verification(db_session, report.id, VerificationRequest(status="VERIFIED", verifier_reference="reviewer_1"))
    result = submit_verification(db_session, report.id, VerificationRequest(status="REJECTED", verifier_reference="reviewer_2", note="reconsidered"))

    assert len(result.history) == 2
    assert result.history[1].previous_status == "VERIFIED"
    assert result.history[1].new_status == "REJECTED"
    assert result.verification_status == "REJECTED"


def test_get_history_does_not_require_analyzed(db_session):
    report = make_analyzed_report(db_session, status=ReportStatus.SUBMITTED)
    history = get_verification_history(db_session, report.id)
    assert history.verification_status == "UNVERIFIED"


def test_get_history_nonexistent_report_raises(db_session):
    with pytest.raises(ReportNotFoundError):
        get_verification_history(db_session, uuid.uuid4())
