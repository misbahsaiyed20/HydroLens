"""
A small, hand-labeled, project-internal evaluation dataset for the AI
vision observation pipeline (Sprint 7, Phase 8).

WHAT THIS IS AND ISN'T:
- This is a PROJECT EVALUATION DATASET, not a statistically representative
  real-world benchmark. 8 scenarios is nowhere near enough to claim
  "accuracy" in any general sense.
- Every entry here is SYNTHETIC and MANUALLY LABELED — the "expected"
  indicators are what a person decided a hypothetical photo matching that
  description SHOULD read as, not measurements from a real photograph.
- No real Gemini output is embedded here. run_evaluation.py runs these
  scenarios against either a mocked vision response (default, no network
  call) or, optionally, a real Gemini call if the caller explicitly asks
  for it and supplies real image files (not provided here) — that path is
  intentionally not exercised automatically.
- This dataset exists to make the evaluation methodology reproducible and
  explainable, not to produce a headline accuracy number.
"""

EVALUATION_SCENARIOS = [
    {
        "id": "A_normal",
        "description": "Normal water condition — clear water, no waste, no algae bloom.",
        "expected": {
            "algae_indicator": "none",
            "turbidity_indicator": "clear",
            "visible_waste": False,
            "color_anomaly_present": False,
        },
    },
    {
        "id": "B_unusual_color",
        "description": "Visually unusual coloration (e.g. an off-color tint) with otherwise normal turbidity/algae.",
        "expected": {
            "algae_indicator": "none",
            "turbidity_indicator": "clear",
            "visible_waste": False,
            "color_anomaly_present": True,
        },
    },
    {
        "id": "C_algae_like",
        "description": "Visible algae-like green coloration/texture on the water surface.",
        "expected": {
            "algae_indicator": "high",
            "turbidity_indicator": "cloudy",
            "visible_waste": False,
            "color_anomaly_present": True,
        },
    },
    {
        "id": "D_visible_waste",
        "description": "Litter/debris visibly floating or on the banks, water otherwise clear.",
        "expected": {
            "algae_indicator": "none",
            "turbidity_indicator": "clear",
            "visible_waste": True,
            "color_anomaly_present": False,
        },
    },
    {
        "id": "E_turbid",
        "description": "Cloudy/turbid, opaque-looking water with no visible algae or waste.",
        "expected": {
            "algae_indicator": "none",
            "turbidity_indicator": "opaque",
            "visible_waste": False,
            "color_anomaly_present": False,
        },
    },
    {
        "id": "F_mixed_conflicting",
        "description": "Ambiguous scene — some cloudiness, faint possible algae tint, unclear photo angle.",
        "expected": {
            "algae_indicator": "low",
            "turbidity_indicator": "slightly_cloudy",
            "visible_waste": False,
            "color_anomaly_present": True,
        },
    },
    {
        "id": "G_weak_evidence",
        "description": "Poor image quality (blurry/far away) — indicators should be present but low-confidence.",
        "expected": {
            "algae_indicator": "unclear",
            "turbidity_indicator": "unclear",
            "visible_waste": False,
            "color_anomaly_present": False,
        },
    },
    {
        "id": "H_strong_corroborating",
        "description": "Clear, close-up, good-lighting photo of an obviously abnormal (opaque, algae-heavy) condition.",
        "expected": {
            "algae_indicator": "high",
            "turbidity_indicator": "opaque",
            "visible_waste": False,
            "color_anomaly_present": True,
        },
    },
]
