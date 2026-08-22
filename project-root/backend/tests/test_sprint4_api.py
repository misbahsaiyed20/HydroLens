import uuid

from app.models.enums import ReportStatus
from tests.factories import BASE_LAT, BASE_LON, make_analyzed_report


def test_actionability_endpoint_success(client, db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    for _ in range(4):
        make_analyzed_report(
            db_session, lat=BASE_LAT + 0.0003, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=10
        )

    response = client.get(f"/api/reports/{target.id}/actionability")
    assert response.status_code == 200
    body = response.json()
    for key in (
        "report_id", "confidence_score", "confidence_level", "exposure_risk_level",
        "action_level", "recommended_action", "key_reasons",
        "supporting_report_count", "conflicting_report_count", "baseline",
    ):
        assert key in body
    assert body["action_level"] in ("CONTINUE_MONITORING", "REVIEW_RECOMMENDED", "PRIORITY_REVIEW")
    assert body["exposure_risk_level"] in ("LOW", "MODERATE", "ELEVATED")


def test_actionability_endpoint_nonexistent_report(client):
    response = client.get(f"/api/reports/{uuid.uuid4()}/actionability")
    assert response.status_code == 404


def test_actionability_endpoint_not_analyzed(client, db_session):
    report = make_analyzed_report(db_session, status=ReportStatus.SUBMITTED)
    response = client.get(f"/api/reports/{report.id}/actionability")
    assert response.status_code == 409


def test_fhir_endpoint_success(client, db_session):
    report = make_analyzed_report(db_session, turbidity_indicator="opaque")
    response = client.get(f"/api/reports/{report.id}/fhir")
    assert response.status_code == 200
    body = response.json()
    assert body["resourceType"] == "Observation"
    assert body["status"] == "preliminary"


def test_fhir_endpoint_nonexistent_report(client):
    response = client.get(f"/api/reports/{uuid.uuid4()}/fhir")
    assert response.status_code == 404


def test_fhir_endpoint_not_analyzed(client, db_session):
    report = make_analyzed_report(db_session, status=ReportStatus.SUBMITTED)
    response = client.get(f"/api/reports/{report.id}/fhir")
    assert response.status_code == 409


def test_sprint_1_2_3_endpoints_still_work(client, db_session):
    report = make_analyzed_report(db_session, turbidity_indicator="opaque")

    assert client.get(f"/api/reports/{report.id}").status_code == 200
    assert client.get("/api/reports").status_code == 200
    assert client.get(f"/api/reports/{report.id}/evidence").status_code == 200
    assert client.get("/health").status_code == 200
