"""
Turns an existing EvidenceFusionResult into an operational review
recommendation. This service does NOT recompute confidence — confidence_
service remains the sole authority for that. It only interprets the
already-computed result (confidence_level, supporting/conflicting counts,
baseline deviation, indicator_severity) into one of three action
categories:

    CONTINUE_MONITORING  — no escalation; keep collecting data
    REVIEW_RECOMMENDED   — worth a human environmental officer's attention
    PRIORITY_REVIEW       — strong, corroborated, severe evidence; review first

Deterministic decision order (first matching rule wins):

  1. confidence_level == LOW, or indicator_severity == NONE
        -> CONTINUE_MONITORING
        (either there's nothing abnormal to review, or not enough
        evidence yet to trust what IS abnormal)

  2. confidence_level == HIGH
     AND conflicting_report_count < supporting_report_count (no conflict
         majority — confidence_service already caps HIGH down to MODERATE
         when this isn't true, so this is a defensive re-check, not the
         primary gate)
     AND (indicator_severity == HIGH
          OR supporting_report_count >= PRIORITY_REVIEW_MIN_SUPPORTING_COUNT)
        -> PRIORITY_REVIEW

  3. otherwise (confidence is MODERATE, or HIGH but didn't clear rule 2)
        -> REVIEW_RECOMMENDED

This mirrors the Sprint 3 principle that conflicting evidence must reduce
— never simply be outvoted by — the action level: a report can only reach
PRIORITY_REVIEW when supporting evidence clearly outweighs conflicting
evidence.
"""
from app.config import get_settings
from app.schemas.actionability import ActionabilityResult
from app.schemas.evidence import EvidenceFusionResult
from app.services.evidence_fusion_service import get_evidence_for_report
from app.services.exposure_risk_service import calculate_exposure_risk

settings = get_settings()

ACTION_RECOMMENDED_TEXT = {
    "CONTINUE_MONITORING": "Continue routine monitoring — evidence does not currently meet the threshold for officer review.",
    "REVIEW_RECOMMENDED": "Environmental officer review recommended.",
    "PRIORITY_REVIEW": "Priority environmental officer review recommended — strong, corroborated evidence of an anomaly.",
}


def determine_action(evidence: EvidenceFusionResult) -> tuple[str, list[str]]:
    supporting = len(evidence.supporting_observations)
    conflicting = len(evidence.conflicting_observations)
    reasons: list[str] = []

    if evidence.confidence_level == "LOW" or evidence.indicator_severity == "NONE":
        reasons.append(
            "confidence is LOW or no abnormal indicator was observed on this report"
        )
        return "CONTINUE_MONITORING", reasons

    no_conflict_majority = conflicting < supporting

    if (
        evidence.confidence_level == "HIGH"
        and no_conflict_majority
        and (
            evidence.indicator_severity == "HIGH"
            or supporting >= settings.priority_review_min_supporting_count
        )
    ):
        reasons.append(f"HIGH confidence with {supporting} corroborating report(s)")
        if evidence.indicator_severity == "HIGH":
            reasons.append("indicator severity is HIGH")
        if evidence.baseline.available and evidence.baseline.deviates:
            reasons.append("deviates from the historical baseline")
        return "PRIORITY_REVIEW", reasons

    reasons.append(f"confidence is {evidence.confidence_level}")
    if conflicting and conflicting >= supporting:
        reasons.append("conflicting reports limit escalation to PRIORITY_REVIEW")
    return "REVIEW_RECOMMENDED", reasons


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def build_actionability_result(evidence: EvidenceFusionResult) -> ActionabilityResult:
    """
    Combines the existing evidence-fusion result with this sprint's action
    and exposure-risk determinations. Kept as a pure function of `evidence`
    (no DB access) so it's trivially unit-testable against hand-built
    EvidenceFusionResult fixtures.
    """
    action_level, action_reasons = determine_action(evidence)
    exposure_level, exposure_reasons = calculate_exposure_risk(evidence)

    key_reasons = _dedupe(evidence.evidence_reasons + action_reasons + exposure_reasons)

    return ActionabilityResult(
        report_id=evidence.report_id,
        confidence_score=evidence.confidence_score,
        confidence_level=evidence.confidence_level,
        exposure_risk_level=exposure_level,
        action_level=action_level,
        recommended_action=ACTION_RECOMMENDED_TEXT[action_level],
        key_reasons=key_reasons,
        supporting_report_count=len(evidence.supporting_observations),
        conflicting_report_count=len(evidence.conflicting_observations),
        baseline=evidence.baseline,
    )


def get_actionability_for_report(db, report_id):
    """Fetches the evidence-fusion result for a report and derives its
    actionability. Propagates evidence_fusion_service's own
    ReportNotFoundError / ReportNotAnalyzedError unchanged so the API layer
    can handle both endpoints identically."""
    evidence = get_evidence_for_report(db, report_id)
    return build_actionability_result(evidence)
