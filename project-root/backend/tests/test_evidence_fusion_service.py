import pytest

from app.models.enums import ReportStatus
from app.services.evidence_fusion_service import (
    ReportNotAnalyzedError,
    ReportNotFoundError,
    get_evidence_for_report,
)
from tests.factories import BASE_LAT, BASE_LON, make_analyzed_report


def test_isolated_report_returns_low_confidence(db_session):
    report = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    result = get_evidence_for_report(db_session, report.id)
    assert result.related_report_count == 0
    assert result.confidence_level == "LOW"
    assert result.recommended_action.startswith("Continue monitoring")


def test_corroborating_reports_raise_confidence(db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    for _ in range(4):
        make_analyzed_report(
            db_session, lat=BASE_LAT + 0.0005, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=10
        )

    result = get_evidence_for_report(db_session, target.id)
    assert result.related_report_count == 4
    assert len(result.supporting_observations) == 4
    assert result.confidence_level in ("MODERATE", "HIGH")
    assert result.recommended_action == "Officer verification recommended."


def test_mixed_evidence_reports_conflict(db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    for _ in range(3):
        make_analyzed_report(
            db_session, lat=BASE_LAT + 0.0005, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=10
        )
    make_analyzed_report(db_session, lat=BASE_LAT + 0.0005, lon=BASE_LON, turbidity_indicator="clear", minutes_ago=10)

    result = get_evidence_for_report(db_session, target.id)
    assert len(result.supporting_observations) == 3
    assert len(result.conflicting_observations) == 1


def test_no_baseline_does_not_force_low_confidence_alone(db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    for _ in range(4):
        make_analyzed_report(
            db_session, lat=BASE_LAT + 0.0002, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=5
        )

    result = get_evidence_for_report(db_session, target.id)
    assert result.baseline.available is False
    # Strong corroboration alone should still be enough to clear MODERATE.
    assert result.confidence_level in ("MODERATE", "HIGH")


def test_baseline_deviation_reflected_in_result(db_session):
    for _ in range(6):
        make_analyzed_report(db_session, minutes_ago=300, turbidity_indicator="clear")
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)

    result = get_evidence_for_report(db_session, target.id)
    assert result.baseline.available is True
    assert result.baseline.deviates is True


def test_normal_observation_is_not_flagged_as_anomaly(db_session):
    report = make_analyzed_report(db_session, turbidity_indicator="clear", algae_indicator="none", minutes_ago=5)
    result = get_evidence_for_report(db_session, report.id)
    assert result.condition_summary == "Observation does not indicate an environmental anomaly."
    assert result.recommended_action.startswith("Continue monitoring")


def test_missing_report_raises(db_session):
    import uuid
    with pytest.raises(ReportNotFoundError):
        get_evidence_for_report(db_session, uuid.uuid4())


def test_unanalyzed_report_raises(db_session):
    report = make_analyzed_report(db_session, status=ReportStatus.SUBMITTED)
    with pytest.raises(ReportNotAnalyzedError):
        get_evidence_for_report(db_session, report.id)


def test_result_is_deterministic(db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    for _ in range(2):
        make_analyzed_report(
            db_session, lat=BASE_LAT + 0.0005, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=10
        )

    first = get_evidence_for_report(db_session, target.id)
    second = get_evidence_for_report(db_session, target.id)
    assert first.confidence_score == second.confidence_score
    assert first.confidence_level == second.confidence_level
