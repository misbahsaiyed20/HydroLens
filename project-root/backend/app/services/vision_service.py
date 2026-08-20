"""
Calls the Gemini vision model on a report's photo and returns structured,
observable indicators. This is deliberately the ONLY file that knows about
Gemini — swapping providers later means changing this file, not the API
layer or the orchestration in analysis_service.py.

Scientific boundary: the prompt explicitly forbids diagnosis/outbreak/
contamination-certainty language, per project rules. This service returns
observations, never risk verdicts — that's confidence_service/evidence_
fusion_service's job in a later sprint.
"""
import base64
import json
from pathlib import Path

import httpx

from app.config import get_settings

settings = get_settings()


class VisionAnalysisError(Exception):
    """Raised for any failure that prevents returning usable indicators
    (missing API key, network/HTTP failure, or an unparseable response)."""


INDICATOR_PROMPT = """You are assisting an environmental-monitoring pipeline that reviews \
citizen photos of urban streams. You are NOT diagnosing disease, predicting an outbreak, or \
declaring the water contaminated. You are only describing what is visually observable in the \
photo.

Return ONLY a JSON object with exactly these keys:
- "algae_indicator": one of "none", "low", "moderate", "high", "unclear"
- "color_anomaly": a short phrase describing any off-color appearance (e.g. "greenish tint", \
"murky brown"), or "none" if the water looks a typical clear/natural color
- "visible_waste": true or false — is litter/debris/waste visibly floating or on the banks?
- "turbidity_indicator": one of "clear", "slightly_cloudy", "cloudy", "opaque", "unclear"
- "image_quality": one of "good", "blurry", "poor_lighting", "too_far", "unclear"
- "model_confidence": a number from 0.0 to 1.0 for how confident you are in these observations \
given the image quality

Base every field only on what is visible in the image. Do not speculate about water safety, \
contamination, or health risk. Return ONLY the JSON object, no other text."""


def _encode_image(image_path: Path) -> tuple[str, str]:
    mime_type = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
    data = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return mime_type, data


def analyze_image(image_path: Path) -> dict:
    """
    Sends a report photo to Gemini and returns a dict of observable
    indicators. Raises VisionAnalysisError on any failure so callers (see
    analysis_service.py) can decide how to handle it — e.g. reverting the
    report's status — without leaking Gemini-specific exceptions upward.
    """
    if not settings.gemini_api_key:
        raise VisionAnalysisError("GEMINI_API_KEY is not configured.")

    if not image_path.exists():
        raise VisionAnalysisError(f"Image file not found: {image_path}")

    mime_type, image_b64 = _encode_image(image_path)

    url = (
        f"{settings.gemini_api_base}/models/{settings.gemini_model}:generateContent"
        f"?key={settings.gemini_api_key}"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": INDICATOR_PROMPT},
                    {"inline_data": {"mime_type": mime_type, "data": image_b64}},
                ]
            }
        ],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    try:
        response = httpx.post(url, json=payload, timeout=30.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise VisionAnalysisError(f"Gemini request failed: {exc}") from exc

    try:
        body = response.json()
        text = body["candidates"][0]["content"]["parts"][0]["text"]
        indicators = json.loads(text)
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        raise VisionAnalysisError(f"Couldn't parse Gemini response: {exc}") from exc

    return indicators
