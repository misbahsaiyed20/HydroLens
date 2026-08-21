from app.services.baseline_service import get_location_baseline
from tests.factories import BASE_LAT, BASE_LON, make_analyzed_report


def test_no_historical_observations_means_no_baseline(db_session):
    target = make_analyzed_report(db_session, minutes_ago=5)
    baseline = get_location_baseline(db_session, target)
    assert baseline.available is False
    assert baseline.deviates is None


def test_sparse_history_below_minimum_means_no_baseline(db_session):
    target = make_analyzed_report(db_session, minutes_ago=5)
    # Only 3 historical reports, older than the event window (default minimum is 5)
    for _ in range(3):
        make_analyzed_report(db_session, minutes_ago=300, turbidity_indicator="clear")

    baseline = get_location_baseline(db_session, target)
    assert baseline.available is False


def test_normal_history_produces_baseline(db_session):
    for _ in range(6):
        make_analyzed_report(db_session, minutes_ago=300, turbidity_indicator="clear", algae_indicator="none")
    target = make_analyzed_report(db_session, minutes_ago=5, turbidity_indicator="clear", algae_indicator="none")

    baseline = get_location_baseline(db_session, target)
    assert baseline.available is True
    assert baseline.turbidity_baseline == "clear"
    assert baseline.deviates is False


def test_deviating_observation_flagged_against_baseline(db_session):
    for _ in range(6):
        make_analyzed_report(db_session, minutes_ago=300, turbidity_indicator="clear", algae_indicator="none")
    target = make_analyzed_report(db_session, minutes_ago=5, turbidity_indicator="opaque", algae_indicator="none")

    baseline = get_location_baseline(db_session, target)
    assert baseline.available is True
    assert baseline.deviates is True


def test_recent_reports_excluded_from_baseline_to_avoid_circularity(db_session):
    # These are recent (inside the event window), so they must NOT count as
    # "historical normal" even though there are enough of them.
    for _ in range(6):
        make_analyzed_report(db_session, minutes_ago=15, turbidity_indicator="opaque")
    target = make_analyzed_report(db_session, minutes_ago=5, turbidity_indicator="opaque")

    baseline = get_location_baseline(db_session, target)
    assert baseline.available is False


def test_waste_rate_deviation(db_session):
    for _ in range(6):
        make_analyzed_report(db_session, minutes_ago=300, visible_waste=False)
    target = make_analyzed_report(db_session, minutes_ago=5, visible_waste=True)

    baseline = get_location_baseline(db_session, target)
    assert baseline.waste_rate == 0.0
    assert baseline.deviates is True
