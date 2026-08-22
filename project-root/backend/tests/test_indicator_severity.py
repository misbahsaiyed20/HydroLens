from app.services.indicator_scales import get_indicator_severity
from tests.factories import make_analyzed_report


def test_no_indicators_is_none_severity(db_session):
    report = make_analyzed_report(db_session, turbidity_indicator="clear", algae_indicator="none", visible_waste=False, color_anomaly="none")
    assert get_indicator_severity(report.observation) == "NONE"


def test_color_anomaly_floors_at_low(db_session):
    report = make_analyzed_report(db_session, turbidity_indicator="clear", algae_indicator="none", visible_waste=False, color_anomaly="murky brown")
    assert get_indicator_severity(report.observation) == "LOW"


def test_visible_waste_floors_at_moderate(db_session):
    report = make_analyzed_report(db_session, turbidity_indicator="clear", algae_indicator="none", visible_waste=True, color_anomaly="none")
    assert get_indicator_severity(report.observation) == "MODERATE"


def test_opaque_turbidity_is_high(db_session):
    report = make_analyzed_report(db_session, turbidity_indicator="opaque", algae_indicator="none")
    assert get_indicator_severity(report.observation) == "HIGH"


def test_none_observation_is_none_severity():
    assert get_indicator_severity(None) == "NONE"
