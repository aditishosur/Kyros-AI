import numpy as np
import pandas as pd

from experiments.forecasting.run_forecast_experiment import (
    FEATURE_COLUMNS,
    make_features,
)


def test_next_timestamp_feature_alignment():
    """Features for t+1 must be indexed by t+1 and use history through t."""

    history = pd.DataFrame(
        {
            "timestamp": pd.date_range(
                "2026-01-01 00:00:00",
                periods=30,
                freq="h",
                tz="UTC",
            ),
            "request_count": np.arange(100, 130, dtype=float),
        }
    )

    next_timestamp = (
        history["timestamp"].iloc[-1]
        + pd.Timedelta(hours=1)
    )

    feature_history = pd.concat(
        [
            history,
            pd.DataFrame(
                {
                    "timestamp": [next_timestamp],
                    "request_count": [np.nan],
                }
            ),
        ],
        ignore_index=True,
    )

    features = make_features(feature_history)
    next_features = features.iloc[-1]

    assert next_features["timestamp"] == next_timestamp

    # Calendar features must correspond to t+1.
    assert next_features["hour"] == next_timestamp.hour
    assert next_features["day_of_week"] == next_timestamp.dayofweek

    # lag_1 for t+1 must be y(t).
    assert next_features["lag_1"] == history["request_count"].iloc[-1]

    # lag_3 for t+1 must be y(t-2).
    assert next_features["lag_3"] == history["request_count"].iloc[-3]

    # lag_6 for t+1 must be y(t-5).
    assert next_features["lag_6"] == history["request_count"].iloc[-6]

    # lag_24 for t+1 must be y(t-23).
    assert next_features["lag_24"] == history["request_count"].iloc[-24]

    # The placeholder must not contaminate the features.
    assert not next_features[FEATURE_COLUMNS].isna().any()

def test_recursive_forecast_uses_next_timestamp_features(monkeypatch):
    """Recursive forecasting must request features for t+1, not t."""

    history = pd.DataFrame(
        {
            "timestamp": pd.date_range(
                "2026-01-01 00:00:00",
                periods=30,
                freq="h",
                tz="UTC",
            ),
            "request_count": np.arange(100, 130, dtype=float),
        }
    )

    captured = {}

    class DummyModel:
        def predict(self, x):
            captured["features"] = x.copy()
            return np.array([999.0])

    from experiments.forecasting.run_forecast_experiment import (
        recursive_rf_forecast,
    )

    predictions = recursive_rf_forecast(
        DummyModel(),
        history,
        horizon=1,
    )

    assert predictions == [999.0]

    features = captured["features"].iloc[0]

    next_timestamp = (
        history["timestamp"].iloc[-1]
        + pd.Timedelta(hours=1)
    )

    assert features["hour"] == next_timestamp.hour
    assert features["day_of_week"] == next_timestamp.dayofweek

    assert features["lag_1"] == history["request_count"].iloc[-1]
    assert features["lag_3"] == history["request_count"].iloc[-3]
    assert features["lag_6"] == history["request_count"].iloc[-6]
    assert features["lag_24"] == history["request_count"].iloc[-24]