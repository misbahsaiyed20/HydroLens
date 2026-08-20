import json

import httpx


def _mock_gemini_response(monkeypatch, indicators: dict, status_code: int = 200):
    """Patches app.services.vision_service.httpx.post to return a fake
    Gemini response shaped like the real API's generateContent payload."""

    def _fake_post(*args, **kwargs):
        payload = {
            "candidates": [
                {"content": {"parts": [{"text": json.dumps(indicators)}]}}
            ]
        }
        return httpx.Response(status_code, json=payload, request=httpx.Request("POST", "http://fake"))

    monkeypatch.setattr("app.services.vision_service.httpx.post", _fake_post)


def test_analysis_success_populates_observation(client, monkeypatch, sample_image_bytes):
    _mock_gemini_response(
        monkeypatch,
        {
            "algae_indicator": "moderate",
            "color_anomaly": "greenish tint",
            "visible_waste": True,
            "turbidity_indicator": "cloudy",
            "image_quality": "good",
            "model_confidence": 0.82,
        },
    )

    response = client.post(
        "/api/reports",
        data={"latitude": "23.0225", "longitude": "72.5714"},
        files={"image": ("stream.png", sample_image_bytes, "image/png")},
    )
    report_id = response.json()["id"]

    # BackgroundTasks in TestClient run before the client call returns, so by
    # now analysis has already completed — fetch the report to confirm.
    final = client.get(f"/api/reports/{report_id}").json()

    assert final["status"] == "ANALYZED"
    assert final["observation"] is not None
    assert final["observation"]["algae_indicator"] == "moderate"
    assert final["observation"]["visible_waste"] is True
    assert final["observation"]["model_confidence"] == 0.82


def test_analysis_failure_reverts_to_submitted(client, monkeypatch, sample_image_bytes):
    def _failing_post(*args, **kwargs):
        raise httpx.ConnectError("simulated network failure")

    monkeypatch.setattr("app.services.vision_service.httpx.post", _failing_post)

    response = client.post(
        "/api/reports",
        data={"latitude": "23.0225", "longitude": "72.5714"},
        files={"image": ("stream.png", sample_image_bytes, "image/png")},
    )
    report_id = response.json()["id"]

    final = client.get(f"/api/reports/{report_id}").json()

    assert final["status"] == "SUBMITTED"
    assert final["observation"] is None


def test_analysis_missing_api_key(client, monkeypatch, sample_image_bytes):
    from app.services import vision_service

    monkeypatch.setattr(vision_service.settings, "gemini_api_key", "")

    response = client.post(
        "/api/reports",
        data={"latitude": "23.0225", "longitude": "72.5714"},
        files={"image": ("stream.png", sample_image_bytes, "image/png")},
    )
    report_id = response.json()["id"]

    final = client.get(f"/api/reports/{report_id}").json()

    assert final["status"] == "SUBMITTED"
    assert final["observation"] is None


def test_analysis_unparseable_response_reverts(client, monkeypatch, sample_image_bytes):
    def _fake_post(*args, **kwargs):
        payload = {"candidates": [{"content": {"parts": [{"text": "not valid json"}]}}]}
        return httpx.Response(200, json=payload, request=httpx.Request("POST", "http://fake"))

    monkeypatch.setattr("app.services.vision_service.httpx.post", _fake_post)

    response = client.post(
        "/api/reports",
        data={"latitude": "23.0225", "longitude": "72.5714"},
        files={"image": ("stream.png", sample_image_bytes, "image/png")},
    )
    report_id = response.json()["id"]

    final = client.get(f"/api/reports/{report_id}").json()

    assert final["status"] == "SUBMITTED"
    assert final["observation"] is None
