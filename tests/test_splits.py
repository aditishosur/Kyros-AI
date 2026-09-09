import pandas as pd
import pytest

from experiments.common.splits import normal_training_rows, validate_episode_splits, validate_telemetry_episode_splits


def test_normal_training_rows_excludes_faults_and_non_training_data():
    frame = pd.DataFrame({
        "split": ["train", "train", "validation"],
        "scenario": ["normal", "database_slowdown", "normal"],
    })
    result = normal_training_rows(frame)
    assert len(result) == 1
    assert result.iloc[0]["scenario"] == "normal"


def test_manifest_rejects_duplicate_episode_identifiers():
    manifest = pd.DataFrame({
        "episode_id": ["same", "same"],
        "split": ["train", "test"],
        "start_time_utc": ["2026-01-01", "2026-01-02"],
        "event_end_time_utc": ["", "2026-01-03"],
    })
    with pytest.raises(ValueError, match="unique"):
        validate_episode_splits(manifest)


def test_telemetry_rejects_an_episode_that_straddles_splits():
    telemetry = pd.DataFrame({"episode_id": ["episode-1", "episode-1"], "split": ["train", "validation"]})
    with pytest.raises(ValueError, match="straddle"):
        validate_telemetry_episode_splits(telemetry)
