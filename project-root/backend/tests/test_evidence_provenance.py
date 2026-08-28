from app.models.enums import VerificationStatus
from app.services.evidence_fusion_service import get_evidence_for_report
from tests.factories import BASE_LAT, BASE_LON, make_analyzed_report


def test_unverified_supporting_report_is_identifiable(db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    make_analyzed_report(
        db_session, lat=BASE_LAT + 0.0003, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=10
    )

    result = get_evidence_for_report(db_session, target.id)
    assert result.supporting_observations[0].verification_status == "UNVERIFIED"
    assert result.evidence_provenance.supporting_unverified_count == 1
    assert result.evidence_provenance.supporting_verified_count == 0
    assert "unverified" in " ".join(result.evidence_reasons).lower()


def test_verified_supporting_report_is_identifiable(db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    make_analyzed_report(
        db_session, lat=BASE_LAT + 0.0003, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=10,
        verification_status=VerificationStatus.VERIFIED,
    )

    result = get_evidence_for_report(db_session, target.id)
    assert result.supporting_observations[0].verification_status == "VERIFIED"
    assert result.evidence_provenance.supporting_verified_count == 1
    assert any("human-verified" in r for r in result.evidence_reasons)


def test_rejected_report_is_identifiable(db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    make_analyzed_report(
        db_session, lat=BASE_LAT + 0.0003, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=10,
        verification_status=VerificationStatus.REJECTED,
    )

    result = get_evidence_for_report(db_session, target.id)
    assert result.supporting_observations[0].verification_status == "REJECTED"
    assert result.evidence_provenance.supporting_rejected_count == 1
    assert any("rejected" in r.lower() for r in result.evidence_reasons)


def test_conflicting_evidence_retains_provenance(db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    make_analyzed_report(
        db_session, lat=BASE_LAT + 0.0003, lon=BASE_LON, turbidity_indicator="clear", minutes_ago=10,
        verification_status=VerificationStatus.VERIFIED,
    )

    result = get_evidence_for_report(db_session, target.id)
    assert result.conflicting_observations[0].verification_status == "VERIFIED"
    assert result.evidence_provenance.conflicting_verified_count == 1


def test_evaluated_report_own_verification_status_included(db_session):
    report = make_analyzed_report(db_session, turbidity_indicator="opaque", verification_status=VerificationStatus.VERIFIED)
    result = get_evidence_for_report(db_session, report.id)
    assert result.evidence_provenance.evaluated_report_verification_status == "VERIFIED"


def test_confidence_score_unaffected_by_verification_status(db_session):
    """Verification must not change confidence_service's score — it only
    adds descriptive provenance. Two identical evidence sets, differing
    only in verification_status, must score identically. Uses two
    well-separated locations so the two scenarios' reports don't bleed
    into each other's related-report radius."""
    target_a = make_analyzed_report(db_session, lat=BASE_LAT + 0.05, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=5)
    make_analyzed_report(
        db_session, lat=BASE_LAT + 0.0503, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=10,
        verification_status=VerificationStatus.UNVERIFIED,
    )
    result_unverified = get_evidence_for_report(db_session, target_a.id)

    target_b = make_analyzed_report(db_session, lat=BASE_LAT - 0.05, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=5)
    make_analyzed_report(
        db_session, lat=BASE_LAT - 0.0497, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=10,
        verification_status=VerificationStatus.VERIFIED,
    )
    result_verified = get_evidence_for_report(db_session, target_b.id)

    assert result_unverified.related_report_count == 1
    assert result_verified.related_report_count == 1
    assert result_unverified.confidence_score == result_verified.confidence_score
    assert result_unverified.confidence_level == result_verified.confidence_level
