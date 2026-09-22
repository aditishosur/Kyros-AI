import pandas as pd

from experiments.forecasting.prepare_gentd26_dataset import (
    pd as preparation_pd,
    aggregate_hourly_request_counts
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


def test_hourly_aggregation_zero_fills_and_includes_all_records():
    timestamps = pd.Series(
        pd.to_datetime(
            [
                "2026-01-01 00:15:00",
                "2026-01-01 00:45:00",
                "2026-01-01 02:10:00",
            ],
            utc=True,
        )
    )

    result = aggregate_hourly_request_counts(timestamps)

    expected = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2026-01-01 00:00:00",
                    "2026-01-01 01:00:00",
                    "2026-01-01 02:00:00",
                ],
                utc=True,
            ),
            "request_count": [2, 0, 1],
        }
    )

    pd.testing.assert_frame_equal(result, expected)