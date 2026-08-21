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
