
"""Offline scenario evaluation of the existing Kyros-AI simulation equations.

This evaluates deterministic behavior and consistency, NOT counterfactual
prediction accuracy. Dataset A has no observed post-intervention outcomes.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


DATA_DIR = Path("data/processed/controlled_anomaly")
OUTPUT_DIR = Path("results/simulation_dataset_a_v1")

# Percent changes applied independently to each baseline episode.
SCENARIOS = {
    "no_change": (0.0, 0.0, 0.0),
    "traffic_plus_20": (20.0, 0.0, 0.0),
    "capacity_plus_20": (0.0, 20.0, 0.0),
    "db_latency_plus_20": (0.0, 0.0, 20.0),
    "db_latency_minus_20": (0.0, 0.0, -20.0),
    "traffic_plus_20_capacity_plus_20": (20.0, 20.0, 0.0),
}


def simulate(
    request_rate: float,
    latency: float,
    error_rate: float,
    db_latency: float,
    traffic_change: float,
    capacity_change: float,
    db_latency_change: float,
) -> dict[str, float]:
    """Mirror the existing simulator's request, DB, latency, and error equations."""
    traffic_factor = 1 + traffic_change / 100
    capacity_factor = max(0.25, 1 + capacity_change / 100)
    db_factor = 1 + db_latency_change / 100
    pressure = max(traffic_factor / capacity_factor, 0.1)

    simulated_requests = request_rate * traffic_factor
    simulated_db = db_latency * db_factor * (
        1 + max(pressure - 1, 0) * 0.35
    )
    simulated_latency = (
        latency * (1 + max(pressure - 1, 0) * 0.85)
        + (simulated_db - db_latency) * 0.65
    )
    simulated_error_rate = max(
        0,
        error_rate
        + max(pressure - 1, 0) * 8
        + max(db_factor - 1, 0) * 3,
    )

    return {
        "simulated_request_rate": simulated_requests,
        "simulated_db_latency": simulated_db,
        "simulated_latency": simulated_latency,
        "simulated_error_rate": simulated_error_rate,
    }


def build_episode_baselines(
    telemetry: pd.DataFrame,
    manifest: pd.DataFrame,
    prediction_hour: int = 131,
    window_hours: int = 7,
) -> pd.DataFrame:
    """Use the same post-event evaluation hour as the RCA experiment."""
    required = {
        "episode_id",
        "timestamp",
        "request_count",
        "response_time_ms",
        "db_latency_ms",
        "error_rate",
    }
    missing = required - set(telemetry.columns)
    if missing:
        raise ValueError(f"Missing telemetry columns: {sorted(missing)}")

    rows = []

    for episode in manifest.itertuples(index=False):
        episode_data = (
            telemetry.loc[telemetry["episode_id"] == episode.episode_id]
            .sort_values("timestamp")
            .reset_index(drop=True)
        )

        if len(episode_data) <= prediction_hour:
            raise ValueError(
                f"Insufficient telemetry for episode {episode.episode_id}"
            )

        recent = episode_data.iloc[
            prediction_hour - window_hours + 1 : prediction_hour + 1
        ]

        rows.append(
            {
                "episode_id": episode.episode_id,
                "split": episode.split,
                "primary_cause": episode.primary_cause,
                "request_rate": float(recent["request_count"].mean()),
                "latency": float(recent["response_time_ms"].mean()),
                "error_rate": float(recent["error_rate"].mean()),
                "db_latency": float(recent["db_latency_ms"].mean()),
            }
        )

    return pd.DataFrame(rows)


def evaluate_scenarios(baselines: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for episode in baselines.itertuples(index=False):
        for scenario_name, changes in SCENARIOS.items():
            output = simulate(
                request_rate=episode.request_rate,
                latency=episode.latency,
                error_rate=episode.error_rate,
                db_latency=episode.db_latency,
                traffic_change=changes[0],
                capacity_change=changes[1],
                db_latency_change=changes[2],
            )

            rows.append(
                {
                    "episode_id": episode.episode_id,
                    "split": episode.split,
                    "primary_cause": episode.primary_cause,
                    "scenario": scenario_name,
                    "traffic_change_pct": changes[0],
                    "capacity_change_pct": changes[1],
                    "db_latency_change_pct": changes[2],
                    "baseline_request_rate": episode.request_rate,
                    "baseline_latency": episode.latency,
                    "baseline_error_rate": episode.error_rate,
                    "baseline_db_latency": episode.db_latency,
                    **output,
                    "latency_delta": (
                        output["simulated_latency"] - episode.latency
                    ),
                    "error_rate_delta": (
                        output["simulated_error_rate"] - episode.error_rate
                    ),
                }
            )

    return pd.DataFrame(rows)


def summarize_test_scenarios(results: pd.DataFrame) -> pd.DataFrame:
    test = results.loc[results["split"] == "test"]

    return (
        test.groupby("scenario", as_index=False)
        .agg(
            episodes=("episode_id", "nunique"),
            mean_latency_delta=("latency_delta", "mean"),
            mean_error_rate_delta=("error_rate_delta", "mean"),
        )
        .sort_values("scenario")
        .reset_index(drop=True)
    )


def main() -> None:
    telemetry = pd.read_csv(DATA_DIR / "telemetry.csv")
    manifest = pd.read_csv(DATA_DIR / "manifest.csv")

    baselines = build_episode_baselines(telemetry, manifest)
    results = evaluate_scenarios(baselines)
    summary = summarize_test_scenarios(results)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    baselines.to_csv(OUTPUT_DIR / "episode_baselines.csv", index=False)
    results.to_csv(OUTPUT_DIR / "scenario_predictions.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "test_scenario_summary.csv", index=False)

    print(f"Episodes: {len(baselines)}")
    print(f"Scenario predictions: {len(results)}")
    print("\nHeld-out test scenario summary:")
    print(summary.to_string(index=False))
    print(f"\nSaved results to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

