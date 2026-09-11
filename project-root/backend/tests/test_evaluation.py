from evaluation.dataset import EVALUATION_SCENARIOS
from evaluation.run_evaluation import run_evaluation
from app.services.vision_service import VisionAnalysisError


def test_dataset_has_all_eight_scenarios():
    ids = {s["id"] for s in EVALUATION_SCENARIOS}
    assert ids == {
        "A_normal", "B_unusual_color", "C_algae_like", "D_visible_waste",
        "E_turbid", "F_mixed_conflicting", "G_weak_evidence", "H_strong_corroborating",
    }


def test_all_scenarios_skipped_when_no_images_provided():
    report = run_evaluation({})
    summary = report.summary()
    assert summary["dataset_size"] == 8
    assert summary["skipped_no_image"] == 8
    assert summary["evaluated"] == 0


def test_perfect_agreement_scenario():
    def fake_analyze(path):
        return {
            "algae_indicator": "none", "turbidity_indicator": "clear",
            "visible_waste": False, "color_anomaly": "none",
            "image_quality": "good", "model_confidence": 0.9,
        }

    report = run_evaluation({"A_normal": "fake.jpg"}, analyze_fn=fake_analyze)
    result = next(r for r in report.results if r.scenario_id == "A_normal")
    assert result.status == "ok"
    assert all(result.per_indicator_match.values())


def test_disagreement_is_detected():
    def fake_analyze(path):
        return {
            "algae_indicator": "high", "turbidity_indicator": "opaque",  # wrong vs expected "none"/"clear"
            "visible_waste": False, "color_anomaly": "none",
            "image_quality": "good", "model_confidence": 0.9,
        }

    report = run_evaluation({"A_normal": "fake.jpg"}, analyze_fn=fake_analyze)
    result = next(r for r in report.results if r.scenario_id == "A_normal")
    assert result.per_indicator_match["algae_indicator"] is False
    assert result.per_indicator_match["turbidity_indicator"] is False


def test_invalid_output_counted_separately_not_as_disagreement():
    def fake_analyze(path):
        raise VisionAnalysisError("simulated malformed response")

    report = run_evaluation({"A_normal": "fake.jpg"}, analyze_fn=fake_analyze)
    summary = report.summary()
    assert summary["invalid_output_count"] == 1
    assert summary["evaluated"] == 0


def test_summary_never_claims_representative_accuracy():
    report = run_evaluation({})
    summary = report.summary()
    assert "representative" in summary["note"].lower()
    assert "not" in summary["note"].lower()


def test_color_anomaly_presence_compared_not_exact_text():
    def fake_analyze(path):
        return {
            "algae_indicator": "none", "turbidity_indicator": "clear",
            "visible_waste": False, "color_anomaly": "slight greenish tint",  # different wording, still "present"
            "image_quality": "good", "model_confidence": 0.9,
        }

    report = run_evaluation({"B_unusual_color": "fake.jpg"}, analyze_fn=fake_analyze)
    result = next(r for r in report.results if r.scenario_id == "B_unusual_color")
    assert result.per_indicator_match["color_anomaly_present"] is True


def test_evaluation_is_deterministic():
    def fake_analyze(path):
        return {
            "algae_indicator": "none", "turbidity_indicator": "clear",
            "visible_waste": False, "color_anomaly": "none",
            "image_quality": "good", "model_confidence": 0.9,
        }

    r1 = run_evaluation({"A_normal": "fake.jpg"}, analyze_fn=fake_analyze).summary()
    r2 = run_evaluation({"A_normal": "fake.jpg"}, analyze_fn=fake_analyze).summary()
    assert r1 == r2
