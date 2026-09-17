from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from experiments.anomaly.detectors import IsolationForestDetector, RobustLatencyBaseline
from experiments.anomaly.evaluate import detector_metrics, select_threshold
from experiments.anomaly.plots import write_alert_timeline
from experiments.common.run_metadata import write_daily_handoff, write_run_metadata
from experiments.common.splits import normal_training_rows, validate_episode_splits, validate_telemetry_episode_splits
from experiments.scenarios.generator import generate_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the locked anomaly and early-warning evaluation.")
    parser.add_argument("--config", type=Path, default=Path("configs/anomaly_protocol.json"))
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    run_id = args.run_id or f"anomaly_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
    output_dir = Path("results") / run_id
    metrics_dir, predictions_dir, figures_dir = (output_dir / "metrics", output_dir / "predictions", output_dir / "figures")
    for directory in (metrics_dir, predictions_dir, figures_dir):
        directory.mkdir(parents=True, exist_ok=True)

    frame, manifest = generate_dataset(config)
    validate_episode_splits(manifest)
    validate_telemetry_episode_splits(frame)
    train = normal_training_rows(frame)
    validation = frame.loc[frame["split"] == "validation"].copy()
    baseline = RobustLatencyBaseline().fit(train)
    detector = IsolationForestDetector(config["features"], config["iforest_contamination"], config["base_seed"]).fit(train)
    frame["baseline_score"] = baseline.score(frame)
    frame["iforest_score"] = detector.score(frame)
    validation["baseline_score"] = baseline.score(validation)
    validation["iforest_score"] = detector.score(validation)
    baseline_threshold = select_threshold(validation["baseline_score"].to_numpy(), validation, "baseline_score", config["false_alert_budget_per_100_normal_hours"])
    iforest_threshold = select_threshold(validation["iforest_score"].to_numpy(), validation, "iforest_score", config["false_alert_budget_per_100_normal_hours"])
    frame["baseline_alert"] = frame["baseline_score"] >= baseline_threshold
    frame["iforest_alert"] = frame["iforest_score"] >= iforest_threshold
    frame["reactive_score"] = frame[["response_time_ms", "error_rate"]].div(
        [config["reactive_latency_ms"], config["reactive_error_rate_pct"]]
    ).max(axis=1)
    frame["reactive_alert"] = (frame["response_time_ms"] >= config["reactive_latency_ms"]) | (frame["error_rate"] >= config["reactive_error_rate_pct"])

    records, event_tables, false_tables = [], [], []
    for detector_name, score, alert in [
        ("robust_latency_baseline", "baseline_score", "baseline_alert"),
        ("isolation_forest", "iforest_score", "iforest_alert"),
        ("reactive_threshold", "reactive_score", "reactive_alert"),
    ]:
        metrics, event_table, false_table = detector_metrics(frame, manifest, detector_name, score, alert)
        records.append(metrics)
        event_table.insert(0, "detector", detector_name)
        event_tables.append(event_table)
        false_tables.append(false_table)
    pd.DataFrame(records).to_csv(metrics_dir / "anomaly_metrics.csv", index=False)
    pd.concat(event_tables, ignore_index=True).to_csv(metrics_dir / "event_alert_table.csv", index=False)
    pd.concat(false_tables, ignore_index=True).to_csv(metrics_dir / "false_alert_table.csv", index=False)
    frame.to_csv(predictions_dir / "hourly_alert_scores.csv", index=False)
    manifest.to_csv(predictions_dir / "scenario_manifest.csv", index=False)
    write_alert_timeline(frame, figures_dir / "alert_timeline.html")
    write_run_metadata(output_dir / "run_metadata.json", args.config, predictions_dir / "hourly_alert_scores.csv")
    locked = {"iforest_threshold": iforest_threshold, "baseline_threshold": baseline_threshold, "config": config}
    (output_dir / "locked_detector_config.json").write_text(json.dumps(locked, indent=2), encoding="utf-8")
    write_daily_handoff(
        output_dir / "daily_handoff.md",
        run_id,
        f"python -m experiments.anomaly.run_experiment --config {args.config} --run-id {run_id}",
        predictions_dir / "hourly_alert_scores.csv",
        [metrics_dir / "anomaly_metrics.csv", metrics_dir / "event_alert_table.csv", metrics_dir / "false_alert_table.csv", figures_dir / "alert_timeline.html"],
    )
    print(f"Completed {run_id}. Results are in {output_dir}")


if __name__ == "__main__":
    main()
