import uuid

from app.models.enums import ReportStatus
from tests.factories import make_analyzed_report


def test_verify_endpoint_success(client, db_session):
    report = make_analyzed_report(db_session)
    response = client.post(
        f"/api/reports/{report.id}/verify",
        json={"status": "VERIFIED", "verifier_reference": "reviewer_1", "note": "looks right"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verification_status"] == "VERIFIED"
    assert body["latest_verifier_reference"] == "reviewer_1"
    assert body["latest_note"] == "looks right"


def test_verify_endpoint_reject(client, db_session):
    report = make_analyzed_report(db_session)
    response = client.post(
        f"/api/reports/{report.id}/verify",
        json={"status": "REJECTED", "verifier_reference": "reviewer_2"},
    )
    assert response.status_code == 200
    assert response.json()["verification_status"] == "REJECTED"


def test_verify_endpoint_nonexistent_report(client):
    response = client.post(
        f"/api/reports/{uuid.uuid4()}/verify",
        json={"status": "VERIFIED", "verifier_reference": "x"},
    )
    assert response.status_code == 404


def test_verify_endpoint_unanalyzed_report(client, db_session):
    report = make_analyzed_report(db_session, status=ReportStatus.SUBMITTED)
    response = client.post(
        f"/api/reports/{report.id}/verify",
        json={"status": "VERIFIED", "verifier_reference": "x"},
    )
    assert response.status_code == 409


def test_verify_endpoint_invalid_status_is_422(client, db_session):
    report = make_analyzed_report(db_session)
    response = client.post(
        f"/api/reports/{report.id}/verify",
        json={"status": "UNVERIFIED", "verifier_reference": "x"},
    )
    assert response.status_code == 422


def test_verify_endpoint_blank_verifier_is_422(client, db_session):
    report = make_analyzed_report(db_session)
    response = client.post(
        f"/api/reports/{report.id}/verify",
        json={"status": "VERIFIED", "verifier_reference": "   "},
    )
    assert response.status_code == 422


def test_verify_endpoint_missing_verifier_is_422(client, db_session):
    report = make_analyzed_report(db_session)
    response = client.post(f"/api/reports/{report.id}/verify", json={"status": "VERIFIED"})
    assert response.status_code == 422


def test_verification_endpoint_reflects_state(client, db_session):
    report = make_analyzed_report(db_session)
    client.post(f"/api/reports/{report.id}/verify", json={"status": "VERIFIED", "verifier_reference": "reviewer_1"})

    response = client.get(f"/api/reports/{report.id}/verification")
    assert response.status_code == 200
    body = response.json()
    assert body["verification_status"] == "VERIFIED"
    assert len(body["history"]) == 1


def test_verification_endpoint_nonexistent_report(client):
    response = client.get(f"/api/reports/{uuid.uuid4()}/verification")
    assert response.status_code == 404


def test_verify_creates_audit_record_with_actor_and_transition(client, db_session):
    report = make_analyzed_report(db_session)
    client.post(
        f"/api/reports/{report.id}/verify",
        json={"status": "VERIFIED", "verifier_reference": "reviewer_1", "note": "confirmed"},
    )

    history = client.get(f"/api/reports/{report.id}/verification").json()
    event = history["history"][0]
    assert event["report_id"] == str(report.id)
    assert event["previous_status"] == "UNVERIFIED"
    assert event["new_status"] == "VERIFIED"
    assert event["verifier_reference"] == "reviewer_1"
    assert event["note"] == "confirmed"
    assert "created_at" in event and event["created_at"]


def test_report_endpoint_shows_verification_status_distinct_from_ai_status(client, db_session):
    report = make_analyzed_report(db_session)
    body = client.get(f"/api/reports/{report.id}").json()
    assert body["status"] == "ANALYZED"
    assert body["verification_status"] == "UNVERIFIED"


def test_sprint_1_through_4_endpoints_still_work(client, db_session):
    report = make_analyzed_report(db_session, turbidity_indicator="opaque")

    assert client.get(f"/api/reports/{report.id}").status_code == 200
    assert client.get("/api/reports").status_code == 200
    assert client.get(f"/api/reports/{report.id}/evidence").status_code == 200
    assert client.get(f"/api/reports/{report.id}/actionability").status_code == 200
    assert client.get(f"/api/reports/{report.id}/fhir").status_code == 200
    assert client.get("/health").status_code == 200
