"""
Exposure-risk signal: LOW / MODERATE / ELEVATED.

This is NOT a disease prediction, outbreak prediction, or contamination
confirmation. It answers a narrower, deliberately scoped question: "does
the observed environmental condition, combined with how much we trust that
observation, look like something worth flagging for environmental/public-
health review if people might interact with this water?" It says nothing
about who is exposed, whether anyone is at risk, or what illness (if any)
could result — that information doesn't exist in this system and this
service must never imply otherwise.

Deterministic 2-factor lookup table (indicator_severity x confidence_level),
with an optional one-level bump for baseline deviation:

              LOW conf   MODERATE conf   HIGH conf
  NONE          LOW          LOW           LOW
  LOW           LOW          LOW           MODERATE
  MODERATE      LOW          MODERATE      ELEVATED
  HIGH          MODERATE     ELEVATED      ELEVATED

indicator_severity comes from indicator_scales.get_indicator_severity (the
same label used by actionability_service) — i.e. how abnormal THIS
report's photo indicators look. confidence_level comes from
confidence_service via the evidence-fusion result — i.e. how much corroborated
evidence supports that abnormality being real and not noise. A severe-
looking but uncorroborated single report is deliberately kept lower than a
severe, well-corroborated one.

Baseline deviation (when a baseline is available) bumps the result up one
level, capped at ELEVATED, because a condition genuinely unusual for that
specific location is more actionable than one that merely looks bad in
isolation.
"""
from app.schemas.evidence import EvidenceFusionResult

_LEVELS = ["LOW", "MODERATE", "ELEVATED"]

_MATRIX = {
    ("NONE", "LOW"): "LOW", ("NONE", "MODERATE"): "LOW", ("NONE", "HIGH"): "LOW",
    ("LOW", "LOW"): "LOW", ("LOW", "MODERATE"): "LOW", ("LOW", "HIGH"): "MODERATE",
    ("MODERATE", "LOW"): "LOW", ("MODERATE", "MODERATE"): "MODERATE", ("MODERATE", "HIGH"): "ELEVATED",
    ("HIGH", "LOW"): "MODERATE", ("HIGH", "MODERATE"): "ELEVATED", ("HIGH", "HIGH"): "ELEVATED",
}


def calculate_exposure_risk(evidence: EvidenceFusionResult) -> tuple[str, list[str]]:
    level = _MATRIX[(evidence.indicator_severity, evidence.confidence_level)]
    reasons = [
        f"indicator severity {evidence.indicator_severity} combined with "
        f"{evidence.confidence_level} evidence confidence"
    ]

    if evidence.baseline.available and evidence.baseline.deviates and level != "ELEVATED":
        idx = _LEVELS.index(level)
        level = _LEVELS[min(idx + 1, len(_LEVELS) - 1)]
        reasons.append("historical baseline deviation raised the exposure-risk signal")

    return level, reasons
