from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "timestamp",
    "endpoint",
    "request_count",
    "response_time_ms",
    "error_rate",
    "cpu_usage",
    "db_latency_ms",
}


def load_nab_windows(windows_path: Path, series_key: str) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Load one NAB series' official labelled anomaly windows."""
    windows = json.loads(windows_path.read_text(encoding="utf-8"))
    if series_key not in windows:
        raise ValueError(f"NAB series key not found in labels: {series_key}")
    return [
        (pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC"))
        for start, end in windows[series_key]
    ]


def adapt_nab_series(
    source_path: Path,
    windows_path: Path,
    series_key: str,
    output_path: Path,
) -> tuple[pd.DataFrame, dict]:
    """Preserve a NAB signal and materialize its official anomaly windows as labels.

    The NAB value remains a generic source metric. It is deliberately not mapped
    to latency, request count, CPU, database latency, or error rate.
    """
    source = pd.read_csv(source_path)
    if not {"timestamp", "value"}.issubset(source.columns):
        raise ValueError("NAB source must contain timestamp and value columns")
    adapted = source.loc[:, ["timestamp", "value"]].copy()
    adapted["timestamp"] = pd.to_datetime(adapted["timestamp"], utc=True, errors="raise")
    adapted = adapted.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)
    adapted = adapted.rename(columns={"value": "source_metric_value"})
    adapted["endpoint"] = series_key
    windows = load_nab_windows(windows_path, series_key)
    adapted["event_label"] = False
    adapted["event_id"] = pd.NA
    for event_index, (start, end) in enumerate(windows, start=1):
        inside = adapted["timestamp"].between(start, end, inclusive="both")
        adapted.loc[inside, "event_label"] = True
        adapted.loc[inside, "event_id"] = f"nab_event_{event_index}"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    adapted.to_csv(output_path, index=False)
    report = {
        "dataset": "Numenta Anomaly Benchmark",
        "series_key": series_key,
        "source_path": str(source_path),
        "windows_path": str(windows_path),
        "row_count": int(len(adapted)),
        "event_windows": len(windows),
        "labelled_rows": int(adapted["event_label"].sum()),
        "available_kyros_features": ["timestamp", "endpoint"],
        "source_metric_column": "source_metric_value",
        "limitation": "This is a labelled, univariate NAB result. It is not multivariate API telemetry validation and has no independent warning window for lead-time evaluation.",
    }
    return adapted, report


def load_mapping(mapping_path: Path) -> dict:
    """Read a deliberately explicit source-column to Kyros-column mapping."""
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    if "columns" not in mapping:
        raise ValueError("Dataset B mapping must contain a 'columns' object")
    return mapping


def adapt_dataset_b(source_path: Path, mapping_path: Path, output_path: Path) -> tuple[pd.DataFrame, dict]:
    """Adapt real telemetry without fabricating fields that are absent in the source."""
    mapping = load_mapping(mapping_path)
    source = pd.read_csv(source_path)
    rename = {source_column: kyros_column for source_column, kyros_column in mapping["columns"].items()}
    missing_source = set(rename).difference(source.columns)
    if missing_source:
        raise ValueError(f"Dataset B is missing mapped source columns: {sorted(missing_source)}")
    adapted = source.rename(columns=rename).copy()
    available = REQUIRED_COLUMNS.intersection(adapted.columns)
    if "timestamp" not in available:
        raise ValueError("Dataset B requires a timestamp column")
    adapted["timestamp"] = pd.to_datetime(adapted["timestamp"], utc=True, errors="raise")
    if "endpoint" not in adapted:
        adapted["endpoint"] = mapping.get("default_endpoint", "dataset_b_service")
    for column in REQUIRED_COLUMNS.difference(adapted.columns):
        adapted[column] = pd.NA
    label_column = mapping.get("label_column")
    if label_column and label_column in adapted.columns:
        adapted["evaluation_positive"] = adapted[label_column].astype(bool)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    adapted.to_csv(output_path, index=False)
    report = {
        "source_path": str(source_path),
        "available_kyros_features": sorted(available),
        "has_labels": bool(label_column and label_column in adapted.columns),
        "limitation": "Early-warning event metrics require trustworthy event labels with onset times."
        if not (label_column and label_column in adapted.columns)
        else "Labels are present; confirm their event semantics before calculating lead time.",
    }
    return adapted, report


def main() -> None:
    parser = argparse.ArgumentParser(description="Map a verified public telemetry dataset into the Kyros schema.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/processed/dataset_b_telemetry.csv"))
    args = parser.parse_args()
    _, report = adapt_dataset_b(args.source, args.mapping, args.output)
    report_path = args.output.with_name("dataset_b_adapter_report.json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote adapted data to {args.output} and report to {report_path}")


if __name__ == "__main__":
    main()
