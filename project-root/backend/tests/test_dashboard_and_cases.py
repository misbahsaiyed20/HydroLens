import uuid

from app.models.enums import VerificationStatus
from tests.factories import BASE_LAT, BASE_LON, make_analyzed_report


def test_dashboard_summary_real_counts(client, db_session):
    make_analyzed_report(db_session, turbidity_indicator="opaque")
    make_analyzed_report(db_session, turbidity_indicator="clear", verification_status=VerificationStatus.VERIFIED)

    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_reports"] == 2
    assert body["analyzed_reports"] == 2
    assert body["verified_cases"] == 1


def test_dashboard_summary_empty_db(client):
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_reports"] == 0
    assert body["high_confidence_cases"] == 0


def test_cases_list_only_includes_analyzed(client, db_session):
    from app.models.enums import ReportStatus
    make_analyzed_report(db_session, status=ReportStatus.SUBMITTED)
    make_analyzed_report(db_session, turbidity_indicator="opaque")

    resp = client.get("/api/cases")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1


def test_cases_list_filter_by_verification_status(client, db_session):
    make_analyzed_report(db_session, verification_status=VerificationStatus.VERIFIED)
    make_analyzed_report(db_session, verification_status=VerificationStatus.UNVERIFIED)

    resp = client.get("/api/cases?verification_status=VERIFIED")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["verification_status"] == "VERIFIED"


def test_cases_list_filter_by_confidence_level(client, db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    for _ in range(4):
        make_analyzed_report(db_session, lat=BASE_LAT + 0.0003, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=10)

    resp = client.get("/api/cases?confidence_level=HIGH")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert all(item["confidence_level"] == "HIGH" for item in body["items"])


def test_cases_list_empty_state(client):
    resp = client.get("/api/cases")
    assert resp.status_code == 200
    assert resp.json() == {"total": 0, "items": []}


def test_case_detail_success(client, db_session):
    report = make_analyzed_report(db_session, turbidity_indicator="opaque")
    resp = client.get(f"/api/cases/{report.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["report_id"] == str(report.id)
    assert body["fhir_url"] == f"/api/reports/{report.id}/fhir"
    assert "verification_history" in body
    assert "baseline" in body


def test_case_detail_404(client):
    resp = client.get(f"/api/cases/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_case_detail_409_unanalyzed(client, db_session):
    from app.models.enums import ReportStatus
    report = make_analyzed_report(db_session, status=ReportStatus.SUBMITTED)
    resp = client.get(f"/api/cases/{report.id}")
    assert resp.status_code == 409


def test_existing_endpoints_unchanged(client, db_session):
    report = make_analyzed_report(db_session)
    assert client.get(f"/api/reports/{report.id}").status_code == 200
    assert client.get("/api/reports").status_code == 200
    assert client.get(f"/api/reports/{report.id}/evidence").status_code == 200
    assert client.get(f"/api/reports/{report.id}/actionability").status_code == 200
    assert client.get(f"/api/reports/{report.id}/fhir").status_code == 200
    assert client.get(f"/api/reports/{report.id}/verification").status_code == 200
