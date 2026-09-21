
"""Convert controlled hourly telemetry into existing Kyros RCA inputs.

The adapter reproduces the application's recent-versus-earlier traffic
comparison within each independent episode. It does not modify RCA rules.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class RCASignals:
    traffic: float
    db_latency: float
    errors: float
    response_latency: float


def derive_rca_signals(
    episode: pd.DataFrame,
    prediction_time: str | pd.Timestamp,
) -> RCASignals:
    """Derive RCA signals using observations available at prediction_time."""

    required = {
        "timestamp",
        "request_count",
        "response_time_ms",
        "error_rate",
        "db_latency_ms",
    }

    missing = required.difference(episode.columns)
    if missing:
        raise ValueError(f"Missing telemetry columns: {sorted(missing)}")

    if episode.empty:
        raise ValueError("Cannot derive RCA signals from an empty episode")

    if "episode_id" in episode.columns and episode["episode_id"].nunique() != 1:
        raise ValueError("Expected telemetry from exactly one episode")

    frame = episode.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame = frame.sort_values("timestamp")

    target_time = pd.to_datetime(prediction_time, utc=True)

    if not frame["timestamp"].eq(target_time).any():
        raise ValueError("Prediction timestamp does not exist in episode")

    frame = frame.loc[frame["timestamp"] <= target_time]

    window_start = target_time - pd.Timedelta(hours=6)

    recent = frame.loc[frame["timestamp"] >= window_start]
    baseline = frame.loc[frame["timestamp"] < window_start]

    if baseline.empty:
        raise ValueError("Insufficient earlier history for traffic baseline")

    baseline_requests = max(float(baseline["request_count"].mean()), 1.0)
    recent_requests = float(recent["request_count"].mean())

    traffic_delta = (
        (recent_requests - baseline_requests) / baseline_requests * 100
    )

    mean_db_latency = float(recent["db_latency_ms"].mean())
    mean_response_latency = float(recent["response_time_ms"].mean())

    # Dataset A supplies error-rate percentages directly rather than
    # individual HTTP status-code records.
    mean_error_rate = float(recent["error_rate"].mean())

    return RCASignals(
        traffic=round(traffic_delta, 1),
        db_latency=round((mean_db_latency / 90 - 1) * 100, 1),
        errors=round(mean_error_rate, 1),
        response_latency=round(
            (mean_response_latency / 300 - 1) * 100, 1
        ),
    )
