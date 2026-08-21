from app.schemas.evidence import BaselineSummary
from app.services.confidence_service import calculate_confidence
from app.services.related_report_service import find_related_reports
from tests.factories import BASE_LAT, BASE_LON, make_analyzed_report

NO_BASELINE = BaselineSummary(available=False, historical_observation_count=0)


def test_single_isolated_report_is_low_confidence(db_session):
    report = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    result = calculate_confidence(report, [], NO_BASELINE)
    assert result.level == "LOW"
    assert 0.0 <= result.score <= 1.0


def test_multiple_corroborating_reports_raise_confidence(db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    for _ in range(4):
        make_analyzed_report(db_session, lat=BASE_LAT + 0.0005, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=10)
    related = find_related_reports(db_session, target)

    result = calculate_confidence(target, related, NO_BASELINE)
    assert len(result.supporting) == 4
    assert result.level in ("MODERATE", "HIGH")


def test_conflicting_reports_reduce_confidence(db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    for _ in range(4):
        make_analyzed_report(db_session, lat=BASE_LAT + 0.0005, lon=BASE_LON, turbidity_indicator="clear", minutes_ago=10)
    related = find_related_reports(db_session, target)

    result = calculate_confidence(target, related, NO_BASELINE)
    assert len(result.conflicting) == 4
    assert len(result.supporting) == 0
    assert result.level == "LOW"


def test_conflict_caps_high_confidence(db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    for _ in range(4):
        make_analyzed_report(db_session, lat=BASE_LAT + 0.0005, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=10)
    for _ in range(4):
        make_analyzed_report(db_session, lat=BASE_LAT + 0.0005, lon=BASE_LON, turbidity_indicator="clear", minutes_ago=10)
    related = find_related_reports(db_session, target)

    result = calculate_confidence(
        target, related, BaselineSummary(available=True, historical_observation_count=10, deviates=True)
    )
    # Support == conflict count -> safety cap must prevent HIGH even with a
    # deviating baseline pushing the raw weighted score up.
    assert result.level != "HIGH"


def test_poor_image_quality_lowers_score(db_session):
    good = make_analyzed_report(db_session, turbidity_indicator="opaque", image_quality="good", minutes_ago=5)
    blurry = make_analyzed_report(db_session, turbidity_indicator="opaque", image_quality="blurry", minutes_ago=5)

    good_result = calculate_confidence(good, [], NO_BASELINE)
    blurry_result = calculate_confidence(blurry, [], NO_BASELINE)
    assert blurry_result.score < good_result.score


def test_baseline_deviation_increases_score(db_session):
    report = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    deviating = BaselineSummary(available=True, historical_observation_count=10, deviates=True)
    not_deviating = BaselineSummary(available=True, historical_observation_count=10, deviates=False)

    result_deviates = calculate_confidence(report, [], deviating)
    result_normal = calculate_confidence(report, [], not_deviating)
    assert result_deviates.score > result_normal.score


def test_recent_scores_higher_than_old(db_session):
    recent = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=1)
    old = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=119)

    recent_result = calculate_confidence(recent, [], NO_BASELINE)
    old_result = calculate_confidence(old, [], NO_BASELINE)
    assert recent_result.score > old_result.score


def test_geographic_clustering_increases_score(db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=5)
    tight = make_analyzed_report(db_session, lat=BASE_LAT + 0.0002, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=5)
    loose = make_analyzed_report(db_session, lat=BASE_LAT + 0.0025, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=5)

    from app.services.related_report_service import RelatedReport
    tight_related = [RelatedReport(tight, 22.0, 5.0, False)]
    loose_related = [RelatedReport(loose, 278.0, 5.0, False)]

    tight_score = calculate_confidence(target, tight_related, NO_BASELINE).score
    loose_score = calculate_confidence(target, loose_related, NO_BASELINE).score
    assert tight_score > loose_score


def test_score_bounds_stay_within_zero_one(db_session):
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=1)
    from app.services.related_report_service import RelatedReport
    supporting = [RelatedReport(target, 0.0, 0.0, True) for _ in range(20)]
    result = calculate_confidence(
        target, supporting, BaselineSummary(available=True, historical_observation_count=10, deviates=True)
    )
    assert 0.0 <= result.score <= 1.0


def test_confidence_level_thresholds(db_session):
    from app.config import get_settings
    from app.services.related_report_service import RelatedReport

    settings = get_settings()
    target = make_analyzed_report(db_session, turbidity_indicator="opaque", minutes_ago=1)
    corroborators = [
        make_analyzed_report(db_session, lat=BASE_LAT, lon=BASE_LON, turbidity_indicator="opaque", minutes_ago=1)
        for _ in range(4)
    ]
    supporting = [RelatedReport(c, 0.0, 0.0, False) for c in corroborators]

    high_result = calculate_confidence(
        target, supporting, BaselineSummary(available=True, historical_observation_count=10, deviates=True)
    )
    assert high_result.score >= settings.confidence_high_threshold
    assert high_result.level == "HIGH"
