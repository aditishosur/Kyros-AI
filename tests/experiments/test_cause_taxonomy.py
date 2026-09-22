import pytest

from experiments.common.cause_taxonomy import (
    APPLICATION_ERROR,
    DB_LATENCY,
    ELEVATED_RISK,
    TRAFFIC_DB_PRESSURE,
    normalize_kyros_cause,
)


def test_normalizes_traffic_db_pressure():
    assert (
        normalize_kyros_cause("Database pressure caused by traffic surge")
        == TRAFFIC_DB_PRESSURE
    )


def test_normalizes_db_latency():
    assert (
        normalize_kyros_cause(
            "Database latency is the primary degradation driver"
        )
        == DB_LATENCY
    )


def test_normalizes_application_error():
    assert normalize_kyros_cause("Application error burst") == APPLICATION_ERROR


def test_normalizes_elevated_risk():
    assert normalize_kyros_cause("Elevated performance risk") == ELEVATED_RISK


def test_unknown_cause_fails_loudly():
    with pytest.raises(ValueError):
        normalize_kyros_cause("Some new undocumented cause")
