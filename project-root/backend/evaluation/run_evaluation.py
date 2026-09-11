"""
Evaluation harness for the AI vision pipeline (Phase 9).

Usage (real evaluation, requires a GEMINI_API_KEY and real photos):

    from pathlib import Path
    from evaluation.run_evaluation import run_evaluation
    report = run_evaluation({"A_normal": Path("photos/a.jpg"), ...})
    print(report.summary())

This project ships NO real photos and makes NO live Gemini calls
automatically — doing so would violate the "do not make unnecessary
Gemini/API calls" rule and would require real, appropriately-licensed
water-body photos this repo doesn't have. `run_evaluation` is exercised in
automated tests (tests/test_evaluation.py) with a MOCKED vision_service
call, which verifies the comparison/metric logic itself works correctly
and deterministically — it does not, and must not be read as, a claim
about real-world Gemini accuracy.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from evaluation.dataset import EVALUATION_SCENARIOS
from app.services.vision_service import VisionAnalysisError, analyze_image

# Indicators actually compared. `color_anomaly_present` is derived from the
# free-text `color_anomaly` field (present/absent), since the model's exact
# wording isn't meant to match a fixed label.
_COMPARED_INDICATORS = ("algae_indicator", "turbidity_indicator", "visible_waste")


@dataclass
class ScenarioResult:
    scenario_id: str
    status: str  # "ok" | "invalid_output" | "skipped_no_image"
    per_indicator_match: dict = field(default_factory=dict)  # indicator -> bool
    model_output: Optional[dict] = None
    error: Optional[str] = None


@dataclass
class EvaluationReport:
    results: list

    def summary(self) -> dict:
        evaluated = [r for r in self.results if r.status == "ok"]
        invalid = [r for r in self.results if r.status == "invalid_output"]
        skipped = [r for r in self.results if r.status == "skipped_no_image"]

        per_indicator_agreement = {}
        for indicator in _COMPARED_INDICATORS:
            matches = [r.per_indicator_match[indicator] for r in evaluated if indicator in r.per_indicator_match]
            per_indicator_agreement[indicator] = (sum(matches) / len(matches)) if matches else None

        return {
            "dataset_size": len(self.results),
            "evaluated": len(evaluated),
            "skipped_no_image": len(skipped),
            "invalid_output_count": len(invalid),
            "invalid_output_rate": (len(invalid) / len(evaluated + invalid)) if (evaluated or invalid) else None,
            "per_indicator_agreement": per_indicator_agreement,
            "note": (
                "Limited internal evaluation over a small, hand-labeled, synthetic "
                f"scenario set (n={len(self.results)}). NOT a statistically representative "
                "real-world accuracy measurement."
            ),
        }


def _compare(expected: dict, model_output: dict) -> dict:
    match = {}
    for indicator in _COMPARED_INDICATORS:
        match[indicator] = expected.get(indicator) == model_output.get(indicator)

    expected_color = expected.get("color_anomaly_present", False)
    actual_color = bool(model_output.get("color_anomaly")) and model_output.get("color_anomaly", "").strip().lower() not in ("", "none")
    match["color_anomaly_present"] = expected_color == actual_color
    return match


def run_evaluation(
    image_paths: dict,
    analyze_fn: Callable[[Path], dict] = analyze_image,
) -> EvaluationReport:
    """
    `image_paths` maps scenario id -> image file path. Scenarios with no
    provided image are recorded as skipped (not counted as failures).
    `analyze_fn` defaults to the real vision_service.analyze_image but is
    injectable for testing (see tests/test_evaluation.py).
    """
    results = []
    for scenario in EVALUATION_SCENARIOS:
        scenario_id = scenario["id"]
        path = image_paths.get(scenario_id)
        if path is None:
            results.append(ScenarioResult(scenario_id=scenario_id, status="skipped_no_image"))
            continue

        try:
            model_output = analyze_fn(Path(path))
        except VisionAnalysisError as exc:
            results.append(ScenarioResult(scenario_id=scenario_id, status="invalid_output", error=str(exc)))
            continue

        match = _compare(scenario["expected"], model_output)
        results.append(
            ScenarioResult(scenario_id=scenario_id, status="ok", per_indicator_match=match, model_output=model_output)
        )

    return EvaluationReport(results=results)
