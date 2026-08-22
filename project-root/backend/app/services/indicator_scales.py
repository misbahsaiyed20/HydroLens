"""
Ordinal severity for the categorical indicator values Gemini returns
(app/services/vision_service.py's prompt defines these exact value sets).
Centralized here so baseline_service and confidence_service agree on what
"more severe than baseline" means without duplicating the mapping.

"unclear" is intentionally excluded from both scales — an unclear reading
is missing information, not a data point on the severity spectrum, and
should never be silently treated as position 0.
"""

TURBIDITY_SEVERITY = {"clear": 0, "slightly_cloudy": 1, "cloudy": 2, "opaque": 3}
ALGAE_SEVERITY = {"none": 0, "low": 1, "moderate": 2, "high": 3}

# --- Sprint 4: labeled indicator severity, used by actionability + exposure-risk ---
SEVERITY_LABELS = {0: "NONE", 1: "LOW", 2: "MODERATE", 3: "HIGH"}


def get_indicator_severity(observation) -> str:
    """
    Coarse NONE/LOW/MODERATE/HIGH label for a single observation, combining
    all indicators (not just the boolean is_abnormal() gate confidence_service
    uses). Sprint 4's actionability and exposure-risk services key off this
    label rather than re-deriving their own severity logic, so there is one
    place that defines "how bad does this photo's indicators look".

    visible_waste is floored at MODERATE (litter/debris is a fairly
    unambiguous visual signal, even without a graded scale for it).
    color_anomaly is floored at LOW (a described off-color is a real signal,
    but a text description carries less certainty than a categorical scale).
    """
    if observation is None:
        return "NONE"

    level = 0
    if observation.turbidity_indicator in TURBIDITY_SEVERITY:
        level = max(level, TURBIDITY_SEVERITY[observation.turbidity_indicator])
    if observation.algae_indicator in ALGAE_SEVERITY:
        level = max(level, ALGAE_SEVERITY[observation.algae_indicator])
    if observation.visible_waste:
        level = max(level, 2)
    if observation.color_anomaly and observation.color_anomaly.strip().lower() not in ("", "none"):
        level = max(level, 1)

    return SEVERITY_LABELS[level]
