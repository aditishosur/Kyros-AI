from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.preprocessing import RobustScaler

from experiments.anomaly.dataset_b import adapt_nab_series
from experiments.anomaly.evaluate import alert_intervals
from experiments.common.run_metadata import file_sha256


def chronological_split(frame: pd.DataFrame) -> pd.DataFrame:
    """Assign chronological 60/20/20 row splits without random shuffling."""
    result = frame.sort_values("timestamp").reset_index(drop=True).copy()
    train_end = int(len(result) * 0.60)
    validation_end = int(len(result) * 0.80)
    result["split"] = "test"
    result.loc[: train_end - 1, "split"] = "train"
    result.loc[train_end: validation_end - 1, "split"] = "validation"
    return result


def score_isolation_forest(frame: pd.DataFrame, contamination: float = 0.02) -> pd.DataFrame:
    """Fit a univariate model only on normal rows in the chronological train split."""
    result = frame.copy()
    train_normal = result.loc[(result["split"] == "train") & ~result["event_label"], ["source_metric_value"]]
    if len(train_normal) < 10:
        raise ValueError("Dataset B has fewer than 10 normal training observations")
    scaler = RobustScaler().fit(train_normal)
    model = IsolationForest(contamination=contamination, random_state=42, n_estimators=250)
    model.fit(scaler.transform(train_normal))
    result["anomaly_score"] = -model.score_samples(scaler.transform(result[["source_metric_value"]]))
    return result


def event_rows(frame: pd.DataFrame, split: str) -> pd.DataFrame:
    """Only score label windows fully inside one split; exclude split-straddling events."""
    scoped = frame.loc[frame["event_id"].notna()].copy()
    summary = scoped.groupby("event_id", as_index=False).agg(
        first_time=("timestamp", "min"), last_time=("timestamp", "max"), splits=("split", lambda x: set(x))
    )
    return summary.loc[summary["splits"].apply(lambda values: values == {split})].drop(columns="splits")


def choose_threshold(frame: pd.DataFrame, budget_per_100_normal_rows: float) -> float:
    validation = frame.loc[frame["split"] == "validation"].copy()
    candidates = np.unique(np.quantile(validation["anomaly_score"], np.linspace(0.85, 0.999, 80)))
    # Pass the full frame to retain evidence that an official NAB window
    # straddles a split, even though scoring itself uses validation only.
    events = event_rows(frame, "validation")
    records = []
    for threshold in candidates:
        probe = validation.copy()
        probe["alert"] = probe["anomaly_score"] >= threshold
        normal = probe.loc[~probe["event_label"]]
        false_count = len(alert_intervals(normal, "alert"))
        detected = sum(
            probe.loc[probe["event_id"] == event.event_id, "alert"].any()
            for event in events.itertuples(index=False)
        )
        recall = detected / max(len(events), 1)
        rate = false_count / max(len(normal), 1) * 100
        records.append((float(threshold), recall, rate))
    allowed = [record for record in records if record[2] <= budget_per_100_normal_rows]
    return max(allowed or records, key=lambda record: (record[1], -record[2], record[0]))[0]


def evaluate_test(frame: pd.DataFrame, threshold: float) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    test = frame.loc[frame["split"] == "test"].copy()
    test["alert"] = test["anomaly_score"] >= threshold
    events = event_rows(test, "test")
    event_table = events.copy()
    event_table["detected"] = [test.loc[test["event_id"] == event.event_id, "alert"].any() for event in events.itertuples(index=False)]
    normal = test.loc[~test["event_label"]].copy()
    false_table = alert_intervals(normal.assign(false_alert=normal["alert"]), "false_alert")
    false_table["reason"] = "Alert outside an official NAB anomaly window"
    y_true = test["event_label"].astype(int)
    detected = int(event_table["detected"].sum()) if not event_table.empty else 0
    false_alerts = len(false_table)
    precision = detected / max(detected + false_alerts, 1)
    recall = detected / max(len(event_table), 1)
    metrics = {
        "dataset": "NAB",
        "evaluation_type": "univariate labelled anomaly-window validation",
        "event_recall": recall,
        "event_precision": precision,
        "event_f1": 2 * precision * recall / max(precision + recall, 1e-9),
        "pr_auc": float(average_precision_score(y_true, test["anomaly_score"])) if y_true.nunique() == 2 else np.nan,
        "roc_auc": float(roc_auc_score(y_true, test["anomaly_score"])) if y_true.nunique() == 2 else np.nan,
        "false_alerts": false_alerts,
        "false_alert_rate_per_100_normal_rows": false_alerts / max(len(normal), 1) * 100,
        "warning_lead_time": "not valid for NAB",
        "test_events_eligible": int(len(event_table)),
    }
    return metrics, event_table, false_table


def main() -> None:
    parser = argparse.ArgumentParser(description="Run limited external NAB anomaly validation.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--windows", type=Path, required=True)
    parser.add_argument("--series-key", required=True)
    parser.add_argument("--run-id", default="dataset_b_nab_001")
    parser.add_argument("--false-alert-budget", type=float, default=1.0)
    args = parser.parse_args()
    output = Path("results") / args.run_id
    output.mkdir(parents=True, exist_ok=True)
    frame, report = adapt_nab_series(args.source, args.windows, args.series_key, output / "adapted_nab_series.csv")
    frame = score_isolation_forest(chronological_split(frame))
    threshold = choose_threshold(frame, args.false_alert_budget)
    metrics, event_table, false_table = evaluate_test(frame, threshold)
    frame.to_csv(output / "hourly_or_source_interval_scores.csv", index=False)
    event_table.to_csv(output / "event_alert_table.csv", index=False)
    false_table.to_csv(output / "false_alert_table.csv", index=False)
    (output / "adapter_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (output / "run_metadata.json").write_text(json.dumps({
        "run_id": args.run_id,
        "source_sha256": file_sha256(args.source),
        "windows_sha256": file_sha256(args.windows),
        "threshold_selected_on_validation_only": threshold,
        "split": "chronological 60/20/20; split-straddling events excluded",
        "limitation": report["limitation"],
    }, indent=2), encoding="utf-8")
    print(f"Completed {args.run_id}. Results are in {output}")


if __name__ == "__main__":
    main()
