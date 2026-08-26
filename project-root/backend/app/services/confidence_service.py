"""
Deterministic, explainable confidence scoring for a report's evidence set.
No ML model, no LLM call — every sub-score is a plain arithmetic function
of stored data, chosen so another developer (or a reviewer) can trace
exactly why a report received the score it did.

WEIGHTS (sum to 1.0):

    Corroboration (count of independent agreeing reports):   30%
    Recency:                                                  15%
    Geographic consistency:                                   15%
    Indicator agreement (ratio of nearby reports that agree): 15%
    Image quality:                                             10%
    Baseline deviation:                                        15%

Corroboration is weighted highest because the project's stated core idea is
"what can we trust when many people observe differently" — agreement across
independent observers is the central signal, not any single photo's
content.

Corroboration vs. indicator agreement are deliberately two different
components: corroboration is a saturating COUNT (more agreeing reports is
better, up to a cap), while agreement is a RATIO (what fraction of nearby
reports agree — a noisy 4-agree/6-conflict set scores lower here than a
clean 4-agree/0-conflict set, even though both have the same corroboration
count).

INDEPENDENCE LIMITATION (documented, not solved, in Sprint 3): there is no
reporter identity/source verification yet, so "corroboration" currently
just counts report rows — it cannot tell five reports from five different
people apart from five reports from one person re-submitting. To avoid
rewarding duplicate spam, corroboration_score saturates at
CORROBORATION_SATURATION_COUNT reports rather than scaling linearly
forever. Stronger independence verification is left for a later sprint.
"""
from dataclasses import dataclass, field
from statistics import mean

from app.config import get_settings
from app.models.observation import Observation
from app.models.report import Report
from app.schemas.evidence import BaselineSummary
from app.services.indicator_scales import ALGAE_SEVERITY, TURBIDITY_SEVERITY
from app.services.related_report_service import RelatedReport
from app.services.time_utils import to_naive_utc, utc_now_naive

settings = get_settings()

IMAGE_QUALITY_SCORES = {"good": 1.0, "blurry": 0.4, "poor_lighting": 0.4, "too_far": 0.3}
DEFAULT_IMAGE_QUALITY_SCORE = 0.3  # "unclear" or missing

WEIGHT_CORROBORATION = 0.30
WEIGHT_RECENCY = 0.15
WEIGHT_GEOGRAPHIC = 0.15
WEIGHT_AGREEMENT = 0.15
WEIGHT_IMAGE_QUALITY = 0.10
WEIGHT_BASELINE = 0.15


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def is_abnormal(observation: Observation | None) -> bool:
    """Coarse "does this observation support an anomaly" gate. Category-
    level nuance (which indicator, how severe) lives in evidence_reasons,
    not in this boolean."""
    if observation is None:
        return False
    if observation.turbidity_indicator in TURBIDITY_SEVERITY and TURBIDITY_SEVERITY[observation.turbidity_indicator] >= 2:
        return True
    if observation.algae_indicator in ALGAE_SEVERITY and ALGAE_SEVERITY[observation.algae_indicator] >= 2:
        return True
    if observation.visible_waste:
        return True
    if observation.color_anomaly and observation.color_anomaly.strip().lower() not in ("", "none"):
        return True
    return False


@dataclass
class ConfidenceResult:
    score: float
    level: str
    supporting: list[RelatedReport]
    conflicting: list[RelatedReport]
    reasons: list[str] = field(default_factory=list)


def calculate_confidence(
    report: Report, related: list[RelatedReport], baseline: BaselineSummary
) -> ConfidenceResult:
    eval_abnormal = is_abnormal(report.observation)

    # Only meaningful to talk about "supporting"/"conflicting" evidence when
    # the evaluated report itself claims an anomaly. If it doesn't, nearby
    # abnormal reports aren't corroborating THIS report — they're evidence
    # about something else nearby, out of scope for this result.
    if eval_abnormal:
        supporting = [r for r in related if is_abnormal(r.report.observation)]
        conflicting = [r for r in related if not is_abnormal(r.report.observation)]
    else:
        supporting = []
        conflicting = []

    n_related = len(related)

    corroboration_score = (
        min(len(supporting) / settings.corroboration_saturation_count, 1.0) if n_related else 0.0
    )
    agreement_score = (len(supporting) / n_related) if n_related else 0.0

    now = utc_now_naive()
    ages_minutes = [
        (now - to_naive_utc(r.report.submitted_at)).total_seconds() / 60 for r in supporting
    ] + [(now - to_naive_utc(report.submitted_at)).total_seconds() / 60]
    recency_score = _clip01(1 - (mean(ages_minutes) / settings.related_report_time_window_minutes))

    if supporting:
        avg_distance = mean(r.distance_meters for r in supporting)
        geographic_score = _clip01(1 - (avg_distance / settings.related_report_radius_meters))
    else:
        geographic_score = 0.0

    quality_values = [report.observation.image_quality] + [
        r.report.observation.image_quality for r in supporting
    ]
    image_quality_score = mean(
        IMAGE_QUALITY_SCORES.get(q, DEFAULT_IMAGE_QUALITY_SCORE) for q in quality_values
    )

    # Baseline contributes only when it exists AND deviates — absence of a
    # baseline contributes 0, neither penalizing nor inflating the score.
    baseline_score = 1.0 if (baseline.available and baseline.deviates) else 0.0

    score = _clip01(
        corroboration_score * WEIGHT_CORROBORATION
        + recency_score * WEIGHT_RECENCY
        + geographic_score * WEIGHT_GEOGRAPHIC
        + agreement_score * WEIGHT_AGREEMENT
        + image_quality_score * WEIGHT_IMAGE_QUALITY
        + baseline_score * WEIGHT_BASELINE
    )

    if score >= settings.confidence_high_threshold:
        level = "HIGH"
    elif score >= settings.confidence_moderate_threshold:
        level = "MODERATE"
    else:
        level = "LOW"

    # Conflict safety cap: conflicting evidence at least as large as
    # supporting evidence must prevent a HIGH classification, even if the
    # weighted score alone clears the threshold.
    if conflicting and len(conflicting) >= len(supporting) and level == "HIGH":
        level = "MODERATE"

    reasons: list[str] = []
    if supporting:
        reasons.append(
            f"{len(supporting)} corroborating observation(s) within "
            f"{int(settings.related_report_radius_meters)}m / "
            f"{settings.related_report_time_window_minutes} minutes"
        )
    if supporting and geographic_score >= 0.5:
        reasons.append("supporting reports are geographically clustered")
    if recency_score >= 0.5:
        reasons.append("observations are recent")
    if baseline.available and baseline.deviates:
        reasons.append("deviates from the historical baseline for this location")
    elif baseline.available:
        reasons.append("consistent with the historical baseline for this location")
    else:
        reasons.append("no historical baseline available for this location yet")
    if conflicting:
        reasons.append(f"{len(conflicting)} nearby observation(s) report normal conditions")
    if image_quality_score < 0.5:
        reasons.append("image quality is limited, reducing confidence")

    return ConfidenceResult(
        score=score, level=level, supporting=supporting, conflicting=conflicting, reasons=reasons
    )
