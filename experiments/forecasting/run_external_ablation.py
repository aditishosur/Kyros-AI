
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import experiments.forecasting.run_forecast_experiment as base
from experiments.forecasting.run_external_forecast import (
    DATA_PATH,
    RESULTS_ROOT,
    SERIES_NAME,
    calculate_external_metrics,
    chronological_split_external,
    evaluate_external_model,
    load_external_series,
    select_rf_configuration,
    verify_external_split,
)


RUN_ID = datetime.now(timezone.utc).strftime(
    "%Y%m%dT%H%M%SZ"
)

OUTPUT_ROOT = (
    RESULTS_ROOT
    / RUN_ID
    / "dataset_b_gentd26_ablation"
)


def sha256_file(path: Path) -> str:
    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            sha256.update(chunk)

    return sha256.hexdigest()


def get_git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout.strip()

    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
    ):
        return "unknown"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_variant(
    variant_name: str,
    feature_columns: list[str],
) -> pd.DataFrame:

    print(f"\nRunning variant: {variant_name}")
    print(f"Features: {feature_columns}")

    original_features = base.FEATURE_COLUMNS

    try:
        base.FEATURE_COLUMNS = feature_columns

        data = load_external_series()

        train, validation, test = (
            chronological_split_external(data)
        )

        verify_external_split(
            train,
            validation,
            test,
        )

        best_config, selection = (
            select_rf_configuration(
                train,
                validation,
            )
        )

        full_train = pd.concat(
            [train, validation],
            ignore_index=True,
        )

        model = base.fit_rf(
            full_train,
            best_config,
        )

        predictions = evaluate_external_model(
            model_name="RF",
            model=model,
            full_data=data,
            origins=test["timestamp"].tolist(),
            horizons=base.HORIZONS,
            run_id=RUN_ID,
        )

        metrics = calculate_external_metrics(
            predictions
        )

        metrics["variant"] = variant_name

        output_dir = OUTPUT_ROOT / variant_name
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        predictions.to_csv(
            output_dir / "test_predictions.csv",
            index=False,
        )

        metrics.to_csv(
            output_dir / "test_metrics.csv",
            index=False,
        )

        selection.to_csv(
            output_dir / "rf_validation_selection.csv",
            index=False,
        )

        metadata = {
            "run_id": RUN_ID,
            "dataset": "GenTD26",
            "series": SERIES_NAME,
            "variant": variant_name,
            "data_path": str(DATA_PATH),
            "input_sha256": sha256_file(DATA_PATH),
            "git_commit": get_git_commit(),
            "created_at_utc": utc_now_iso(),
            "random_state": base.RANDOM_STATE,
            "horizons": base.HORIZONS,
            "feature_columns": feature_columns,
            "rf_config": best_config,
            "split": {
                "train_fraction": 0.60,
                "validation_fraction": 0.20,
                "train_rows": len(train),
                "validation_rows": len(validation),
                "test_rows": len(test),
            },
            "protocol_notes": [
                "GenTD26 timestamps are used for ordering.",
                "The series is already hourly and is not resampled.",
                "RF is selected using validation only.",
                "Test observations are not used for model fitting.",
                "Test observations are used as rolling history.",
                "Each ablation variant selects its RF configuration independently.",
            ],
        }

        with (
            output_dir / "run_metadata.json"
        ).open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                metadata,
                file,
                indent=2,
                default=str,
            )

        return metrics

    finally:
        base.FEATURE_COLUMNS = original_features


def main() -> None:

    full_features = list(base.FEATURE_COLUMNS)

    ablation_features = [
        feature
        for feature in full_features
        if feature != "lag_24"
    ]

    full_metrics = run_variant(
        variant_name="full",
        feature_columns=full_features,
    )

    ablation_metrics = run_variant(
        variant_name="without_lag24",
        feature_columns=ablation_features,
    )

    comparison = pd.concat(
        [
            full_metrics,
            ablation_metrics,
        ],
        ignore_index=True,
    )

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    comparison.to_csv(
        OUTPUT_ROOT / "comparison_metrics.csv",
        index=False,
    )

    print("\nAblation complete.")
    print(f"Results directory: {OUTPUT_ROOT}")
    print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()