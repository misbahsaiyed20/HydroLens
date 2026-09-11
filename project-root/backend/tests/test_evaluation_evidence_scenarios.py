"""
Phase 10: deterministic evaluation scenarios for the evidence-fusion /
confidence / actionability pipeline. Each test is one of the 8 required
scenarios, verifying the behavior is deterministic, explainable, and
consistent with the documented rules in confidence_service.py /
actionability_service.py — not re-deriving the formula, just exercising it
against known configurations and asserting stable, correct outcomes.
"""
from app.models.enums import VerificationStatus
from app.services.evidence_fusion_service import get_evidence_for_report
from tests.factories import BASE_LAT, BASE_LON, make_analyzed_report


def test_scenario_1_isolated_report(db_session):
    report = make_analyzed_report(db_session, turbidity_indicator="opaque")
    result = get_evidence_for_report(db_session, report.id)
    assert result.related_report_count == 0
    assert result.confidence_level == "LOW"


def test_scenario_2_multiple_agreeing_reports(db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    for _ in range(4):
        make_analyzed_report(db_session, lat=BASE_LAT + 0.0003, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=10)
    result = get_evidence_for_report(db_session, target.id)
    assert len(result.supporting_observations) == 4
    assert result.confidence_level in ("MODERATE", "HIGH")


def test_scenario_3_conflicting_reports(db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    for _ in range(4):
        make_analyzed_report(db_session, lat=BASE_LAT + 0.0003, lon=BASE_LON, turbidity_indicator="clear", minutes_ago=10)
    result = get_evidence_for_report(db_session, target.id)
    assert len(result.conflicting_observations) == 4
    assert result.confidence_level == "LOW"


def test_scenario_4_baseline_deviation(db_session):
    for _ in range(6):
        make_analyzed_report(db_session, minutes_ago=300, turbidity_indicator="clear")
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    result = get_evidence_for_report(db_session, target.id)
    assert result.baseline.available is True
    assert result.baseline.deviates is True


def test_scenario_5_insufficient_historical_baseline(db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque")
    result = get_evidence_for_report(db_session, target.id)
    assert result.baseline.available is False
    assert result.baseline.deviates is None  # absence of data, never treated as "normal" or "abnormal"


def test_scenario_6_verified_supporting_evidence(db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    make_analyzed_report(
        db_session, lat=BASE_LAT + 0.0003, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=10,
        verification_status=VerificationStatus.VERIFIED,
    )
    result = get_evidence_for_report(db_session, target.id)
    assert result.evidence_provenance.supporting_verified_count == 1
    assert any("human-verified" in r for r in result.evidence_reasons)


def test_scenario_7_rejected_evidence(db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    make_analyzed_report(
        db_session, lat=BASE_LAT + 0.0003, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=10,
        verification_status=VerificationStatus.REJECTED,
    )
    result = get_evidence_for_report(db_session, target.id)
    assert result.evidence_provenance.supporting_rejected_count == 1
    # REJECTED evidence is flagged, not silently excluded from scoring (documented limitation)
    assert len(result.supporting_observations) == 1


def test_scenario_8_mixed_provenance(db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    make_analyzed_report(db_session, lat=BASE_LAT + 0.0002, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=10, verification_status=VerificationStatus.VERIFIED)
    make_analyzed_report(db_session, lat=BASE_LAT + 0.0003, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=10, verification_status=VerificationStatus.UNVERIFIED)
    make_analyzed_report(db_session, lat=BASE_LAT + 0.0004, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=10, verification_status=VerificationStatus.REJECTED)

    result = get_evidence_for_report(db_session, target.id)
    p = result.evidence_provenance
    assert p.supporting_verified_count == 1
    assert p.supporting_unverified_count == 1
    assert p.supporting_rejected_count == 1


def test_determinism_across_repeated_calls(db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    make_analyzed_report(db_session, lat=BASE_LAT + 0.0003, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=10)
    r1 = get_evidence_for_report(db_session, target.id)
    r2 = get_evidence_for_report(db_session, target.id)
    assert r1.confidence_score == r2.confidence_score
    assert r1.confidence_level == r2.confidence_level
