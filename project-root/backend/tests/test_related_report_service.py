from app.models.enums import ReportStatus
from app.services.related_report_service import find_related_reports
from tests.factories import BASE_LAT, BASE_LON, make_analyzed_report


def test_nearby_recent_report_is_related(db_session):
    target = make_analyzed_report(db_session, minutes_ago=10)
    make_analyzed_report(db_session, lat=BASE_LAT + 0.001, lon=BASE_LON, minutes_ago=15)  # ~111m away

    related = find_related_reports(db_session, target)
    assert len(related) == 1


def test_far_away_report_is_not_related(db_session):
    target = make_analyzed_report(db_session, minutes_ago=10)
    make_analyzed_report(db_session, lat=BASE_LAT + 0.05, lon=BASE_LON, minutes_ago=10)  # ~5.5km away

    related = find_related_reports(db_session, target)
    assert related == []


def test_old_report_is_not_related(db_session):
    target = make_analyzed_report(db_session, minutes_ago=10)
    make_analyzed_report(db_session, lat=BASE_LAT, lon=BASE_LON, minutes_ago=500)  # way outside window

    related = find_related_reports(db_session, target)
    assert related == []


def test_boundary_radius_and_window(db_session):
    target = make_analyzed_report(db_session, minutes_ago=10)
    # Just inside radius (~270m) and window (115 min)
    make_analyzed_report(db_session, lat=BASE_LAT + 0.0024, lon=BASE_LON, minutes_ago=115)

    related = find_related_reports(db_session, target)
    assert len(related) == 1


def test_missing_stream_name_does_not_crash(db_session):
    target = make_analyzed_report(db_session, minutes_ago=5, stream_name=None)
    make_analyzed_report(db_session, lat=BASE_LAT, lon=BASE_LON, minutes_ago=5, stream_name=None)

    related = find_related_reports(db_session, target)
    assert len(related) == 1
    assert related[0].same_stream_name is False


def test_matching_stream_name_flagged(db_session):
    target = make_analyzed_report(db_session, minutes_ago=5, stream_name="Sabarmati")
    make_analyzed_report(db_session, lat=BASE_LAT, lon=BASE_LON, minutes_ago=5, stream_name="sabarmati ")

    related = find_related_reports(db_session, target)
    assert related[0].same_stream_name is True


def test_unanalyzed_report_is_excluded(db_session):
    target = make_analyzed_report(db_session, minutes_ago=5)
    make_analyzed_report(db_session, lat=BASE_LAT, lon=BASE_LON, minutes_ago=5, status=ReportStatus.SUBMITTED)

    related = find_related_reports(db_session, target)
    assert related == []


def test_report_with_no_location_handled_safely(db_session):
    target = make_analyzed_report(db_session, minutes_ago=5)
    target.location = None  # simulate a missing/invalid location without touching the DB row

    related = find_related_reports(db_session, target)
    assert related == []
