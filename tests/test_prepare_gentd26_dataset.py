
import pandas as pd

from experiments.forecasting.prepare_gentd26_dataset import (
    aggregate_hourly_request_counts,
)


def test_hourly_aggregation_zero_fills_and_includes_all_raw_records():
    raw = pd.DataFrame(
        {
            "gmt_create": [
                "2026-01-01 00:15:00",
                "2026-01-01 00:45:00",
                "2026-01-01 02:10:00",
            ],
            "predict_type": [
                "TXT_2_IMG",
                "IMG_2_IMG",
                "INPAINTING",
            ],
            "predict_status": [
                "created",
                "success",
                "failed",
            ],
        }
    )

    result = aggregate_hourly_request_counts(raw)

    expected = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2026-01-01 00:00:00",
                    "2026-01-01 01:00:00",
                    "2026-01-01 02:00:00",
                ]
            ),
            "request_count": [2, 0, 1],
        }
    )

    pd.testing.assert_frame_equal(result, expected)