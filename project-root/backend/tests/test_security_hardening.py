import httpx

from app.services.storage_service import _EXTENSION_BY_CONTENT_TYPE
from app.services.vision_service import VisionAnalysisError, _validate_indicators


def test_health_endpoint_no_secrets(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "key" not in str(body).lower()
    assert "secret" not in str(body).lower()
    assert "password" not in str(body).lower()


def test_upload_filename_traversal_is_ignored(client, sample_image_bytes):
    """A malicious filename must never influence the stored path — only
    the validated content-type does."""
    response = client.post(
        "/api/reports",
        data={"latitude": "23.0", "longitude": "72.5"},
        files={"image": ("../../../etc/passwd.png", sample_image_bytes, "image/png")},
    )
    assert response.status_code == 201
    body = response.json()
    assert ".." not in body["image_path"]
    assert "/" not in body["image_path"]
    assert body["image_path"].endswith(_EXTENSION_BY_CONTENT_TYPE["image/png"])


def test_upload_rejects_mismatched_extension_trust():
    # Extension always comes from content-type map, never client filename.
    assert set(_EXTENSION_BY_CONTENT_TYPE.keys()) == {"image/jpeg", "image/png", "image/webp"}


def test_vision_output_validation_rejects_bad_enum_value():
    bad = {
        "algae_indicator": "extremely high", "color_anomaly": "green", "visible_waste": False,
        "turbidity_indicator": "clear", "image_quality": "good", "model_confidence": 0.9,
    }
    try:
        _validate_indicators(bad)
        assert False, "should have raised"
    except VisionAnalysisError:
        pass


def test_vision_output_validation_rejects_out_of_range_confidence():
    bad = {
        "algae_indicator": "none", "color_anomaly": "none", "visible_waste": False,
        "turbidity_indicator": "clear", "image_quality": "good", "model_confidence": 1.5,
    }
    try:
        _validate_indicators(bad)
        assert False, "should have raised"
    except VisionAnalysisError:
        pass


def test_vision_output_validation_rejects_wrong_type():
    bad = {
        "algae_indicator": "none", "color_anomaly": "none", "visible_waste": "yes",
        "turbidity_indicator": "clear", "image_quality": "good", "model_confidence": 0.9,
    }
    try:
        _validate_indicators(bad)
        assert False, "should have raised"
    except VisionAnalysisError:
        pass


def test_vision_output_validation_rejects_missing_field():
    bad = {"algae_indicator": "none", "color_anomaly": "none", "visible_waste": False}
    try:
        _validate_indicators(bad)
        assert False, "should have raised"
    except VisionAnalysisError:
        pass


def test_vision_output_validation_accepts_valid():
    good = {
        "algae_indicator": "none", "color_anomaly": "none", "visible_waste": False,
        "turbidity_indicator": "clear", "image_quality": "good", "model_confidence": 0.9,
    }
    assert _validate_indicators(good) == good


def test_malformed_ai_output_reverts_report_to_submitted(client, monkeypatch, sample_image_bytes):
    def _fake_post(*a, **k):
        payload = {"candidates": [{"content": {"parts": [{"text": '{"algae_indicator": "extremely high"}'}]}}]}
        return httpx.Response(200, json=payload, request=httpx.Request("POST", "http://fake"))

    monkeypatch.setattr("app.services.vision_service.httpx.post", _fake_post)

    resp = client.post(
        "/api/reports",
        data={"latitude": "23.0", "longitude": "72.5"},
        files={"image": ("stream.png", sample_image_bytes, "image/png")},
    )
    report_id = resp.json()["id"]
    final = client.get(f"/api/reports/{report_id}").json()
    assert final["status"] == "SUBMITTED"
    assert final["observation"] is None


def test_unhandled_exception_returns_generic_500_not_traceback(db_session, reviewer_user, monkeypatch):
    from fastapi.testclient import TestClient

    from app.api import cases as cases_api
    from app.core.security import create_access_token
    from app.database import get_db
    from app.main import app

    def _boom(*a, **k):
        raise RuntimeError("simulated internal failure with sensitive detail: db_password=hunter2")

    monkeypatch.setattr(cases_api, "list_cases", _boom)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    token = create_access_token(reviewer_user.id, reviewer_user.role.value)
    # raise_server_exceptions=False: we're specifically testing that the
    # app's own exception handler converts this to a clean response,
    # not letting the test client re-raise for debugging purposes.
    with TestClient(app, raise_server_exceptions=False) as local_client:
        resp = local_client.get("/api/cases", headers={"Authorization": f"Bearer {token}"})
    app.dependency_overrides.clear()

    assert resp.status_code == 500
    assert resp.json() == {"detail": "Internal server error."}
    assert "hunter2" not in resp.text
