import uuid

from app.models.enums import ReportStatus
from tests.factories import BASE_LAT, BASE_LON, make_analyzed_report


def test_evidence_endpoint_valid_report(client, db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    for _ in range(4):
        make_analyzed_report(
            db_session, lat=BASE_LAT + 0.0005, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=10
        )

    response = client.get(f"/api/reports/{target.id}/evidence")
    assert response.status_code == 200
    body = response.json()
    assert body["report_id"] == str(target.id)
    assert body["related_report_count"] == 4
    assert body["confidence_level"] in ("MODERATE", "HIGH")
    assert "recommended_action" in body


def test_evidence_endpoint_nonexistent_report(client):
    response = client.get(f"/api/reports/{uuid.uuid4()}/evidence")
    assert response.status_code == 404


def test_evidence_endpoint_not_yet_analyzed(client, db_session):
    report = make_analyzed_report(db_session, status=ReportStatus.SUBMITTED)
    response = client.get(f"/api/reports/{report.id}/evidence")
    assert response.status_code == 409


def test_evidence_endpoint_insufficient_evidence_still_200(client, db_session):
    report = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    response = client.get(f"/api/reports/{report.id}/evidence")
    assert response.status_code == 200
    assert response.json()["confidence_level"] == "LOW"


def test_evidence_endpoint_malformed_id(client):
    response = client.get("/api/reports/not-a-uuid/evidence")
    assert response.status_code == 422


def test_existing_report_endpoints_still_work(client, db_session):
    report = make_analyzed_report(db_session)
    response = client.get(f"/api/reports/{report.id}")
    assert response.status_code == 200
    assert client.get("/api/reports").status_code == 200
