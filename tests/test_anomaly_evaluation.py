import pandas as pd

from experiments.anomaly.evaluate import alert_intervals


def test_adjacent_alerts_are_counted_as_one_interval():
    frame = pd.DataFrame({
        "endpoint": ["/payments"] * 4,
        "timestamp": pd.to_datetime(["2026-01-01T00:00Z", "2026-01-01T01:00Z", "2026-01-01T02:00Z", "2026-01-01T05:00Z"]),
        "alert": [True, True, True, True],
    })
    intervals = alert_intervals(frame, "alert")
    assert len(intervals) == 2
    assert intervals.iloc[0]["duration_hours"] == 3
