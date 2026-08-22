import uuid

from app.schemas.evidence import BaselineSummary, EvidenceFusionResult, RelatedObservationSummary
from app.services.actionability_service import build_actionability_result, determine_action

NO_BASELINE = BaselineSummary(available=False, historical_observation_count=0)
DEVIATING_BASELINE = BaselineSummary(available=True, historical_observation_count=10, deviates=True)


def _obs_summary():
    return RelatedObservationSummary(report_id=uuid.uuid4(), distance_meters=10.0, minutes_apart=5.0)


def _evidence(
    confidence_level,
    indicator_severity,
    supporting=0,
    conflicting=0,
    baseline=NO_BASELINE,
    confidence_score=0.5,
):
    return EvidenceFusionResult(
        report_id=uuid.uuid4(),
        confidence_score=confidence_score,
        confidence_level=confidence_level,
        indicator_severity=indicator_severity,
        condition_summary="test",
        related_report_count=supporting + conflicting,
        supporting_observations=[_obs_summary() for _ in range(supporting)],
        conflicting_observations=[_obs_summary() for _ in range(conflicting)],
        baseline=baseline,
        evidence_reasons=["test reason"],
        recommended_action="test",
    )


def test_isolated_low_confidence_continues_monitoring():
    action, _ = determine_action(_evidence("LOW", "HIGH"))
    assert action == "CONTINUE_MONITORING"


def test_no_abnormal_indicator_continues_monitoring_even_at_high_confidence():
    action, _ = determine_action(_evidence("HIGH", "NONE", supporting=4))
    assert action == "CONTINUE_MONITORING"


def test_moderate_evidence_gets_review_recommended():
    action, _ = determine_action(_evidence("MODERATE", "MODERATE", supporting=2))
    assert action == "REVIEW_RECOMMENDED"


def test_strong_corroborating_evidence_gets_priority_review():
    action, _ = determine_action(_evidence("HIGH", "HIGH", supporting=4, baseline=DEVIATING_BASELINE))
    assert action == "PRIORITY_REVIEW"


def test_conflicting_evidence_prevents_priority_review():
    action, reasons = determine_action(_evidence("HIGH", "HIGH", supporting=3, conflicting=3))
    assert action != "PRIORITY_REVIEW"
    assert any("conflict" in r.lower() for r in reasons)


def test_baseline_deviation_mentioned_in_priority_reasons():
    _, reasons = determine_action(_evidence("HIGH", "HIGH", supporting=4, baseline=DEVIATING_BASELINE))
    assert any("baseline" in r.lower() for r in reasons)


def test_high_severity_alone_can_reach_priority_review_without_min_count():
    # indicator_severity HIGH satisfies the OR-condition even with just 1 supporter
    action, _ = determine_action(_evidence("HIGH", "HIGH", supporting=1))
    assert action == "PRIORITY_REVIEW"


def test_deterministic_output():
    evidence = _evidence("HIGH", "HIGH", supporting=4, baseline=DEVIATING_BASELINE)
    first = determine_action(evidence)
    second = determine_action(evidence)
    assert first == second


def test_build_actionability_result_combines_action_and_exposure():
    evidence = _evidence("HIGH", "HIGH", supporting=4, baseline=DEVIATING_BASELINE, confidence_score=0.9)
    result = build_actionability_result(evidence)
    assert result.action_level == "PRIORITY_REVIEW"
    assert result.exposure_risk_level == "ELEVATED"
    assert result.supporting_report_count == 4
    assert result.conflicting_report_count == 0
    assert result.recommended_action.startswith("Priority environmental officer review")
    assert len(result.key_reasons) == len(set(result.key_reasons))  # deduped
