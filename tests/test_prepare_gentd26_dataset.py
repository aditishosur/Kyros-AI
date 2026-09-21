import pandas as pd

from experiments.forecasting.prepare_gentd26_dataset import (
    pd as preparation_pd,
)


def test_missing_calendar_hour_becomes_zero():
    timestamps = pd.to_datetime(
        [
            "2024-01-01 00:10:00",
            "2024-01-01 02:10:00",
        ]
    )

    hourly = (
        timestamps
        .floor("h")
        .value_counts()
        .sort_index()
        .rename("request_count")
        .to_frame()
    )

    full_index = pd.date_range(
        start=hourly.index.min(),
        end=hourly.index.max(),
        freq="h",
    )

    hourly = hourly.reindex(
        full_index,
        fill_value=0,
    )

    assert hourly.loc[
        pd.Timestamp("2024-01-01 01:00:00"),
        "request_count",
    ] == 0

def aggregate_hourly_request_counts(
    timestamps: pd.Series,
) -> pd.DataFrame:
    hourly = (
        timestamps
        .dt.floor("h")
        .value_counts()
        .sort_index()
        .rename("request_count")
        .to_frame()
    )

    full_index = pd.date_range(
        start=hourly.index.min(),
        end=hourly.index.max(),
        freq="h",
    )

    hourly = hourly.reindex(
        full_index,
        fill_value=0,
    )

    hourly.index.name = "timestamp"

    return hourly.reset_index()