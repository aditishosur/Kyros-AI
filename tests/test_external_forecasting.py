
import pandas as pd
import pytest

from experiments.forecasting.run_external_forecast import (
    SERIES_NAME,
    evaluate_external_model,
)


def make_test_series(n_hours: int = 60) -> pd.DataFrame:
    timestamps = pd.date_range(
        start="2024-01-01 00:00:00",
        periods=n_hours,
        freq="1h",
        tz="UTC",
    )

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "request_count": [
                float((index * 7) % 100)
                for index in range(n_hours)
            ],
        }
    )


def test_external_evaluation_uses_only_past_for_predictions():
    data = make_test_series()

    origin = data.loc[25, "timestamp"]

    predictions = evaluate_external_model(
        model_name="Persistence",
        model=None,
        full_data=data,
        origins=[origin],
        horizons=[1, 6, 12],
        run_id="test",
    )

    assert not predictions.empty
    assert set(predictions["series"]) == {SERIES_NAME}

    expected_prediction = float(
        data.loc[25, "request_count"]
    )

    assert (
        predictions["prediction"]
        == expected_prediction
    ).all()


def test_external_predictions_do_not_change_when_future_actuals_change():
    original_data = make_test_series()

    altered_data = original_data.copy()

    origin = original_data.loc[25, "timestamp"]

    future_mask = (
        altered_data["timestamp"] > origin
    )

    altered_data.loc[
        future_mask,
        "request_count",
    ] += 10000

    original_predictions = evaluate_external_model(
        model_name="Persistence",
        model=None,
        full_data=original_data,
        origins=[origin],
        horizons=[1, 6, 12],
        run_id="original",
    )

    altered_predictions = evaluate_external_model(
        model_name="Persistence",
        model=None,
        full_data=altered_data,
        origins=[origin],
        horizons=[1, 6, 12],
        run_id="altered",
    )

    assert (
        original_predictions["prediction"].tolist()
        == altered_predictions["prediction"].tolist()
    )

    assert (
        original_predictions["actual"].tolist()
        != altered_predictions["actual"].tolist()
    )


def test_external_evaluation_rejects_unknown_model():
    data = make_test_series()

    with pytest.raises(ValueError, match="Unknown model"):
        evaluate_external_model(
            model_name="UnknownModel",
            model=None,
            full_data=data,
            origins=[
                data.loc[25, "timestamp"]
            ],
            horizons=[1],
            run_id="test",
        )