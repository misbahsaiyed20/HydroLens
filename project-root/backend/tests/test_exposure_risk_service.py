import uuid

from app.schemas.evidence import BaselineSummary, EvidenceFusionResult
from app.schemas.verification import EvidenceProvenanceSummary
from app.services.exposure_risk_service import calculate_exposure_risk

NO_BASELINE = BaselineSummary(available=False, historical_observation_count=0)
DEVIATING_BASELINE = BaselineSummary(available=True, historical_observation_count=10, deviates=True)

_NO_PROVENANCE = EvidenceProvenanceSummary(
    evaluated_report_verification_status="UNVERIFIED",
    supporting_verified_count=0, supporting_unverified_count=0, supporting_rejected_count=0,
    conflicting_verified_count=0, conflicting_unverified_count=0, conflicting_rejected_count=0,
)


def _evidence(indicator_severity, confidence_level, confidence_score=0.5, baseline=NO_BASELINE):
    return EvidenceFusionResult(
        report_id=uuid.uuid4(),
        confidence_score=confidence_score,
        confidence_level=confidence_level,
        indicator_severity=indicator_severity,
        condition_summary="test",
        related_report_count=0,
        supporting_observations=[],
        conflicting_observations=[],
        baseline=baseline,
        evidence_reasons=[],
        recommended_action="test",
        evidence_provenance=_NO_PROVENANCE,
    )


def test_no_medical_language_in_reasons():
    banned = ["disease", "outbreak", "diagnos", "illness", "infect"]
    for severity in ("NONE", "LOW", "MODERATE", "HIGH"):
        for level in ("LOW", "MODERATE", "HIGH"):
            _, reasons = calculate_exposure_risk(_evidence(severity, level))
            text = " ".join(reasons).lower()
            for term in banned:
                assert term not in text


def test_low_signal_when_no_severity():
    level, _ = calculate_exposure_risk(_evidence("NONE", "HIGH"))
    assert level == "LOW"


def test_moderate_signal():
    level, _ = calculate_exposure_risk(_evidence("MODERATE", "MODERATE"))
    assert level == "MODERATE"


def test_elevated_signal():
    level, _ = calculate_exposure_risk(_evidence("HIGH", "HIGH"))
    assert level == "ELEVATED"


def test_baseline_deviation_bumps_level_up():
    without = calculate_exposure_risk(_evidence("MODERATE", "MODERATE", baseline=NO_BASELINE))[0]
    with_deviation = calculate_exposure_risk(_evidence("MODERATE", "MODERATE", baseline=DEVIATING_BASELINE))[0]
    assert without == "MODERATE"
    assert with_deviation == "ELEVATED"


def test_bump_caps_at_elevated():
    level, _ = calculate_exposure_risk(_evidence("HIGH", "HIGH", baseline=DEVIATING_BASELINE))
    assert level == "ELEVATED"


def test_result_only_uses_low_moderate_elevated_vocabulary():
    for severity in ("NONE", "LOW", "MODERATE", "HIGH"):
        for conf in ("LOW", "MODERATE", "HIGH"):
            level, _ = calculate_exposure_risk(_evidence(severity, conf))
            assert level in ("LOW", "MODERATE", "ELEVATED")
