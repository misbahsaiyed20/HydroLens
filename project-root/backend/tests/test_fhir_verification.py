from app.models.enums import VerificationStatus
from app.services.evidence_fusion_service import get_evidence_for_report
from app.services.fhir_service import build_fhir_observation
from app.services.verification_service import submit_verification
from app.schemas.verification import VerificationRequest
from tests.factories import make_analyzed_report


def test_unverified_observation_remains_preliminary(db_session):
    report = make_analyzed_report(db_session)
    evidence = get_evidence_for_report(db_session, report.id)
    resource = build_fhir_observation(report, evidence)
    assert resource["status"] == "preliminary"


def test_verified_observation_maps_to_final(db_session):
    report = make_analyzed_report(db_session)
    submit_verification(db_session, report.id, VerificationRequest(status="VERIFIED", verifier_reference="reviewer_1"))
    db_session.refresh(report)

    evidence = get_evidence_for_report(db_session, report.id)
    resource = build_fhir_observation(report, evidence)
    assert resource["status"] == "final"


def test_rejected_observation_maps_to_cancelled(db_session):
    report = make_analyzed_report(db_session)
    submit_verification(db_session, report.id, VerificationRequest(status="REJECTED", verifier_reference="reviewer_1"))
    db_session.refresh(report)

    evidence = get_evidence_for_report(db_session, report.id)
    resource = build_fhir_observation(report, evidence)
    assert resource["status"] == "cancelled"


def test_no_fabricated_patient_data_after_verification(db_session):
    report = make_analyzed_report(db_session)
    submit_verification(db_session, report.id, VerificationRequest(status="VERIFIED", verifier_reference="reviewer_jane_doe"))
    db_session.refresh(report)

    evidence = get_evidence_for_report(db_session, report.id)
    resource = build_fhir_observation(report, evidence)
    assert "patient" not in resource
    # verifier identity is deliberately NOT embedded in the FHIR output
    assert "reviewer_jane_doe" not in str(resource)


def test_environmental_observation_distinct_from_verification_component(db_session):
    report = make_analyzed_report(db_session, turbidity_indicator="opaque")
    submit_verification(db_session, report.id, VerificationRequest(status="VERIFIED", verifier_reference="reviewer_1"))
    db_session.refresh(report)

    evidence = get_evidence_for_report(db_session, report.id)
    resource = build_fhir_observation(report, evidence)
    texts = {c["code"]["text"]: c for c in resource["component"]}
    assert texts["Turbidity indicator"]["valueString"] == "opaque"  # AI observation, untouched
    assert texts["Verification status"]["valueString"] == "VERIFIED"  # separate component
