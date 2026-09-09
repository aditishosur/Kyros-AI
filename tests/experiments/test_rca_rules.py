from backend.services.rca_rules import determine_root_cause


def test_traffic_and_db_pressure_rule():
    cause, _ = determine_root_cause(
        traffic=30,
        db_latency=20,
        errors=0,
    )

    assert cause == "Database pressure caused by traffic surge"


def test_db_latency_rule():
    cause, _ = determine_root_cause(
        traffic=10,
        db_latency=30,
        errors=0,
    )

    assert cause == "Database latency is the primary degradation driver"


def test_application_error_rule():
    cause, _ = determine_root_cause(
        traffic=10,
        db_latency=10,
        errors=8,
    )

    assert cause == "Application error burst"


def test_fallback_rule():
    cause, _ = determine_root_cause(
        traffic=5,
        db_latency=5,
        errors=1,
    )

    assert cause == "Elevated performance risk"


def test_rule_priority_traffic_db_over_errors():
    cause, _ = determine_root_cause(
        traffic=40,
        db_latency=35,
        errors=12,
    )

    assert cause == "Database pressure caused by traffic surge"


def test_rule_priority_db_over_errors():
    cause, _ = determine_root_cause(
        traffic=10,
        db_latency=35,
        errors=12,
    )

    assert cause == "Database latency is the primary degradation driver"


def test_threshold_is_strictly_greater_than_25_for_traffic():
    cause, _ = determine_root_cause(
        traffic=25,
        db_latency=20,
        errors=0,
    )

    assert cause == "Elevated performance risk"


def test_threshold_is_strictly_greater_than_5_for_errors():
    cause, _ = determine_root_cause(
        traffic=0,
        db_latency=0,
        errors=5,
    )

    assert cause == "Elevated performance risk"
