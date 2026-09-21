
import pandas as pd
import pytest

from experiments.rca.input_adapter import derive_rca_signals


def make_episode():
    timestamps = pd.date_range(
        "2026-01-01", periods=20, freq="h", tz="UTC"
    )

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "episode_id": ["episode-1"] * 20,
            "request_count": [100.0] * 13 + [150.0] * 7,
            "response_time_ms": [300.0] * 13 + [450.0] * 7,
            "error_rate": [1.0] * 13 + [6.0] * 7,
            "db_latency_ms": [90.0] * 13 + [117.0] * 7,
        }
    )


def test_derives_expected_signals():
    episode = make_episode()

    result = derive_rca_signals(
        episode, episode["timestamp"].iloc[-1]
    )

    assert result.traffic == 50.0
    assert result.db_latency == 30.0
    assert result.errors == 6.0
    assert result.response_latency == 50.0


def test_future_rows_do_not_change_earlier_prediction():
    episode = make_episode()

    prediction_time = episode["timestamp"].iloc[15]

    before = derive_rca_signals(episode, prediction_time)

    changed = episode.copy()
    changed.loc[changed.index > 15, "request_count"] = 99999.0
    changed.loc[changed.index > 15, "db_latency_ms"] = 99999.0

    after = derive_rca_signals(changed, prediction_time)

    assert before == after


def test_rejects_multiple_episodes():
    episode = make_episode()
    episode.loc[0, "episode_id"] = "another-episode"

    with pytest.raises(ValueError, match="exactly one episode"):
        derive_rca_signals(episode, episode["timestamp"].iloc[-1])


def test_rejects_insufficient_baseline_history():
    episode = make_episode().iloc[:4]

    with pytest.raises(ValueError, match="Insufficient earlier history"):
        derive_rca_signals(episode, episode["timestamp"].iloc[-1])
