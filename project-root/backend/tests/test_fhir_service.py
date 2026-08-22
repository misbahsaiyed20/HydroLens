from app.services.evidence_fusion_service import get_evidence_for_report
from app.services.fhir_service import build_fhir_observation
from tests.factories import make_analyzed_report


def test_resource_type_is_observation(db_session):
    report = make_analyzed_report(db_session, turbidity_indicator="opaque")
    evidence = get_evidence_for_report(db_session, report.id)
    resource = build_fhir_observation(report, evidence)
    assert resource["resourceType"] == "Observation"


def test_required_structure_present(db_session):
    report = make_analyzed_report(db_session)
    evidence = get_evidence_for_report(db_session, report.id)
    resource = build_fhir_observation(report, evidence)
    for key in ("resourceType", "id", "status", "code", "subject", "effectiveDateTime", "component"):
        assert key in resource


def test_status_is_preliminary_not_final(db_session):
    report = make_analyzed_report(db_session)
    evidence = get_evidence_for_report(db_session, report.id)
    resource = build_fhir_observation(report, evidence)
    assert resource["status"] == "preliminary"
    assert resource["status"] != "final"


def test_timestamp_mapping(db_session):
    report = make_analyzed_report(db_session)
    evidence = get_evidence_for_report(db_session, report.id)
    resource = build_fhir_observation(report, evidence)
    assert resource["effectiveDateTime"] == report.submitted_at.isoformat() + "Z"


def test_environmental_indicators_represented_as_components(db_session):
    report = make_analyzed_report(
        db_session, turbidity_indicator="opaque", algae_indicator="high", visible_waste=True, color_anomaly="greenish"
    )
    evidence = get_evidence_for_report(db_session, report.id)
    resource = build_fhir_observation(report, evidence)

    texts = {c["code"]["text"]: c for c in resource["component"]}
    assert texts["Turbidity indicator"]["valueString"] == "opaque"
    assert texts["Algae indicator"]["valueString"] == "high"
    assert texts["Visible waste"]["valueBoolean"] is True
    assert texts["Color anomaly"]["valueString"] == "greenish"
    assert "Evidence-fusion confidence score" in texts
    assert "Evidence-fusion confidence level" in texts


def test_no_patient_fields_present(db_session):
    report = make_analyzed_report(db_session)
    evidence = get_evidence_for_report(db_session, report.id)
    resource = build_fhir_observation(report, evidence)
    assert "patient" not in resource
    assert "subject" in resource
    assert "reference" not in resource["subject"]  # display-only, no fabricated resource id
    resource_str = str(resource).lower()
    for banned in ("diagnos", "patientname", "dob", "date of birth"):
        assert banned not in resource_str


def test_subject_reflects_location(db_session):
    report = make_analyzed_report(db_session, stream_name="Sabarmati")
    evidence = get_evidence_for_report(db_session, report.id)
    resource = build_fhir_observation(report, evidence)
    assert "Sabarmati" in resource["subject"]["display"]
