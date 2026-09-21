from pathlib import Path

import pandas as pd

from experiments.anomaly.dataset_b import adapt_nab_series
from experiments.anomaly.run_dataset_b_evaluation import chronological_split, event_rows


FIXTURES = Path(__file__).parent / "fixtures"


def test_nab_adapter_preserves_source_metric_and_official_windows(monkeypatch):
    monkeypatch.setattr(pd.DataFrame, "to_csv", lambda *args, **kwargs: None)

    adapted, report = adapt_nab_series(
        FIXTURES / "nab_series.csv",
        FIXTURES / "nab_windows.json",
        "real/example.csv",
        Path("ignored.csv"),
    )

    assert "source_metric_value" in adapted
    assert "response_time_ms" not in adapted
    assert adapted["event_label"].tolist() == [False, True, False]
    assert report["event_windows"] == 1


def test_straddling_nab_events_are_excluded_from_split_metric():
    frame = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=10, freq="h", tz="UTC"),
        "event_label": [False, False, False, False, False, True, True, True, False, False],
        "event_id": [None, None, None, None, None, "event_1", "event_1", "event_1", None, None],
    })
    split = chronological_split(frame)
    assert event_rows(split, "validation").empty
    assert event_rows(split, "test").empty
