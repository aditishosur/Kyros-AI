from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from experiments.common.splits import validate_episode_splits, validate_telemetry_episode_splits
from experiments.scenarios.taxonomy import ESSENTIAL_SCENARIOS, SCENARIOS


BASELINES = {
    "/payments": (430, 255, 58, 92),
    "/orders": (520, 185, 42, 66),
    "/inventory": (360, 220, 46, 74),
}


def _normal_signals(seed: int, endpoint: str, hours: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base_request, base_latency, base_cpu, base_db = BASELINES[endpoint]
    hour = np.arange(hours)
    daily = 1 + 0.26 * np.sin((hour % 24 - 8) / 24 * 2 * np.pi)
    weekday = np.where((hour // 24) % 7 < 5, 1.12, 0.84)
    request = np.maximum(30, rng.normal(base_request * daily * weekday, base_request * 0.08))
    latency = np.maximum(35, rng.normal(base_latency, base_latency * 0.07, hours))
    cpu = np.clip(rng.normal(base_cpu, 4.5, hours), 5, 98)
    db = np.maximum(10, rng.normal(base_db, 6.5, hours))
    error = np.clip(rng.normal(1.1, 0.35, hours), 0.05, 3.0)
    return pd.DataFrame({
        "request_count": request.round(1),
        "response_time_ms": latency.round(1),
        "error_rate": error.round(3),
        "cpu_usage": cpu.round(1),
        "db_latency_ms": db.round(1),
    })


def apply_scenario(frame: pd.DataFrame, scenario: str, intensity: float, onset: int, end: int) -> pd.DataFrame:
    """Inject a transparent fault mechanism into a normal telemetry episode."""
    result = frame.copy()
    event = result.index.to_series().between(onset, end - 1)
    ramp = np.linspace(0.65, 1.0, int(event.sum()))
    if scenario == "traffic_spike":
        result.loc[event, "request_count"] *= 1 + intensity * ramp
        result.loc[event, "cpu_usage"] += 8 * intensity * ramp
    elif scenario == "latency_increase":
        result.loc[event, "response_time_ms"] *= 1 + 1.25 * intensity * ramp
    elif scenario == "database_slowdown":
        result.loc[event, "db_latency_ms"] *= 1 + 1.45 * intensity * ramp
        result.loc[event, "response_time_ms"] *= 1 + 0.95 * intensity * ramp
        result.loc[event, "error_rate"] += 3.8 * intensity * ramp
    elif scenario == "error_burst_5xx":
        result.loc[event, "error_rate"] += 12 * intensity * ramp
        result.loc[event, "response_time_ms"] *= 1 + 0.25 * intensity * ramp
    elif scenario != "normal":
        raise ValueError(f"Unsupported scenario: {scenario}")
    result["error_rate"] = result["error_rate"].clip(upper=100)
    return result.round(3)


def _episode(
    episode_id: str,
    split: str,
    scenario: str,
    seed: int,
    intensity: float,
    endpoint: str,
    start: datetime,
    config: dict,
) -> tuple[pd.DataFrame, dict]:
    hours = config["episode_hours"]
    warning_start = config["warning_start_hour"]
    onset = config["event_onset_hour"]
    end = config["event_end_hour"]
    normal = _normal_signals(seed, endpoint, hours)
    telemetry = apply_scenario(normal, scenario, intensity, onset, end)
    timestamps = pd.date_range(start=start, periods=hours, freq="h", tz="UTC")
    definition = SCENARIOS[scenario]
    telemetry.insert(0, "timestamp", timestamps)
    telemetry.insert(1, "episode_id", episode_id)
    telemetry.insert(2, "split", split)
    telemetry.insert(3, "endpoint", endpoint)
    telemetry.insert(4, "scenario", scenario)
    telemetry["is_warning"] = (np.arange(hours) >= warning_start) & (np.arange(hours) < onset) if scenario != "normal" else False
    telemetry["is_event"] = (np.arange(hours) >= onset) & (np.arange(hours) < end) if scenario != "normal" else False
    telemetry["evaluation_positive"] = telemetry["is_warning"] | telemetry["is_event"]
    manifest = {
        "episode_id": episode_id,
        "run_id": config.get("dataset_run_id", "controlled_dataset_v1"),
        "split": split,
        "seed": seed,
        "endpoint": endpoint,
        "scenario": scenario,
        "fault_family": definition.fault_family,
        "primary_cause": definition.primary_cause,
        "severity": "none" if scenario == "normal" else ("moderate" if intensity < 1 else "high"),
        "intensity": intensity,
        "start_time_utc": timestamps[0].isoformat(),
        "warning_start_time_utc": timestamps[warning_start].isoformat() if scenario != "normal" else "",
        "event_onset_time_utc": timestamps[onset].isoformat() if scenario != "normal" else "",
        "event_end_time_utc": timestamps[end - 1].isoformat() if scenario != "normal" else "",
        "intervention_type": "",
        "intervention_value": "",
        "generator_version": "1.0.0",
    }
    return telemetry, manifest


def generate_dataset(config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, manifest_rows = [], []
    cursor = datetime(2026, 1, 1, tzinfo=timezone.utc)
    plans = [
        ("train", "normal", config["train_normal_seeds"], [0.0]),
        ("validation", "normal", config["validation_normal_seeds"], [0.0]),
        ("test", "normal", config["test_normal_seeds"], [0.0]),
    ]
    for split, scenario, seeds, intensities in plans:
        for position, seed in enumerate(seeds):
            episode_id = f"{split}-{scenario}-{seed}"
            telemetry, manifest = _episode(episode_id, split, scenario, seed, intensities[0], config["endpoints"][position % len(config["endpoints"])], cursor, config)
            rows.append(telemetry)
            manifest_rows.append(manifest)
            cursor += timedelta(hours=config["episode_hours"])
    for split, seeds, intensities in [
        ("validation", config["validation_event_seeds"], config["validation_intensities"]),
        ("test", config["test_event_seeds"], config["test_intensities"]),
    ]:
        for scenario_index, scenario in enumerate(ESSENTIAL_SCENARIOS):
            for position, seed in enumerate(seeds):
                intensity = intensities[position % len(intensities)]
                episode_id = f"{split}-{scenario}-{seed}"
                telemetry, manifest = _episode(episode_id, split, scenario, seed, intensity, config["endpoints"][(scenario_index + position) % len(config["endpoints"])], cursor, config)
                rows.append(telemetry)
                manifest_rows.append(manifest)
                cursor += timedelta(hours=config["episode_hours"])
    telemetry = pd.concat(rows, ignore_index=True)
    manifest = pd.DataFrame(manifest_rows)
    validate_episode_splits(manifest)
    validate_telemetry_episode_splits(telemetry)
    return telemetry, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate labelled controlled telemetry episodes.")
    parser.add_argument("--config", type=Path, default=Path("configs/anomaly_protocol.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/controlled_anomaly"))
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    telemetry, manifest = generate_dataset(config)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    telemetry.to_csv(args.output_dir / "telemetry.csv", index=False)
    manifest.to_csv(args.output_dir / "manifest.csv", index=False)
    print(f"Wrote {len(telemetry)} telemetry rows and {len(manifest)} manifest rows to {args.output_dir}")


if __name__ == "__main__":
    main()
