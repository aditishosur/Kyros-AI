
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from experiments.forecasting.run_forecast_experiment import (
    FEATURE_COLUMNS,
    HORIZONS,
    RANDOM_STATE,
    RF_GRID,
    calculate_metrics,
    fit_rf,
    persistence_forecast,
    recursive_rf_forecast,
    seasonal_naive_forecast,
)


# ============================================================
# CONFIGURATION
# ============================================================

DATA_PATH = Path(
    "data/processed/dataset_b_candidate/"
    "gentd26_hourly_request_counts.csv"
)

RESULTS_ROOT = Path("results")

SERIES_NAME = "GenTD26_aggregate"


# ============================================================
# REPRODUCIBILITY HELPERS
# ============================================================

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
    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# DATA LOADING AND VALIDATION
# ============================================================

def load_external_series() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    data = pd.read_csv(DATA_PATH)

    required_columns = {
        "timestamp",
        "request_count",
    }

    missing = required_columns - set(data.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    data = data[
        ["timestamp", "request_count"]
    ].copy()

    data["timestamp"] = pd.to_datetime(
        data["timestamp"],
        utc=True,
    )

    data["request_count"] = pd.to_numeric(
        data["request_count"],
        errors="raise",
    )

    if data["timestamp"].isna().any():
        raise ValueError(
            "Timestamp column contains missing values."
        )

    if data["request_count"].isna().any():
        raise ValueError(
            "Request count contains missing values."
        )

    if data["timestamp"].duplicated().any():
        raise ValueError(
            "Duplicate timestamps detected."
        )

    if (data["request_count"] < 0).any():
        raise ValueError(
            "Request count contains negative values."
        )

    data = (
        data.sort_values("timestamp")
        .reset_index(drop=True)
    )

    expected_timestamps = pd.date_range(
        start=data["timestamp"].min(),
        end=data["timestamp"].max(),
        freq="1h",
        tz="UTC",
    )

    actual_timestamps = pd.DatetimeIndex(
        data["timestamp"]
    )

    if not actual_timestamps.equals(
        expected_timestamps
    ):
        raise ValueError(
            "Dataset is not a continuous hourly series."
        )

    print("External dataset validation: PASS")
    print(f"Rows: {len(data)}")
    print(
        f"Start: {data['timestamp'].min()}"
    )
    print(
        f"End:   {data['timestamp'].max()}"
    )
    print(
        f"Zero-request hours: "
        f"{(data['request_count'] == 0).sum()}"
    )

    return data


# ============================================================
# TEMPORAL SPLIT
# ============================================================

def chronological_split_external(
    data: pd.DataFrame,
    train_fraction: float = 0.60,
    validation_fraction: float = 0.20,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    n_timestamps = len(data)

    if n_timestamps < 3:
        raise ValueError(
            "Dataset must contain at least 3 timestamps."
        )

    train_end = round(
        n_timestamps * train_fraction
    )

    validation_end = (
        train_end
        + round(
            n_timestamps * validation_fraction
        )
    )

    train = data.iloc[
        :train_end
    ].copy()

    validation = data.iloc[
        train_end:validation_end
    ].copy()

    test = data.iloc[
        validation_end:
    ].copy()

    return (
        train.reset_index(drop=True),
        validation.reset_index(drop=True),
        test.reset_index(drop=True),
    )


def verify_external_split(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
) -> None:

    train_ts = set(train["timestamp"])
    validation_ts = set(validation["timestamp"])
    test_ts = set(test["timestamp"])

    if train_ts & validation_ts:
        raise AssertionError(
            "Train/validation overlap detected."
        )

    if validation_ts & test_ts:
        raise AssertionError(
            "Validation/test overlap detected."
        )

    if train_ts & test_ts:
        raise AssertionError(
            "Train/test overlap detected."
        )

    if not (
        train["timestamp"].max()
        < validation["timestamp"].min()
    ):
        raise AssertionError(
            "Train is not strictly before validation."
        )

    if not (
        validation["timestamp"].max()
        < test["timestamp"].min()
    ):
        raise AssertionError(
            "Validation is not strictly before test."
        )

    if train.empty or validation.empty or test.empty:
        raise AssertionError(
            "One or more splits are empty."
        )

    print("External temporal split verification: PASS")
    print(
        f"Train:      {len(train)} timestamps"
    )
    print(
        f"Validation: {len(validation)} timestamps"
    )
    print(
        f"Test:       {len(test)} timestamps"
    )


# ============================================================
# ROLLING-ORIGIN EVALUATION
# ============================================================

def evaluate_external_model(
    model_name: str,
    model,
    full_data: pd.DataFrame,
    origins: list[pd.Timestamp],
    horizons: list[int],
    run_id: str,
) -> pd.DataFrame:

    rows = []
    max_horizon = max(horizons)

    for origin_index, origin in enumerate(
        origins,
        start=1,
    ):

        history = full_data[
            full_data["timestamp"] <= origin
        ][
            ["timestamp", "request_count"]
        ].copy()

        future = full_data[
            full_data["timestamp"] > origin
        ][
            ["timestamp", "request_count"]
        ].copy()

        if len(future) < max_horizon:
            continue

        if model_name == "RF":
            predictions = recursive_rf_forecast(
                model,
                history,
                max_horizon,
            )

        elif model_name == "Persistence":
            predictions = persistence_forecast(
                history,
                max_horizon,
            )

        elif model_name == "SeasonalNaive":
            predictions = seasonal_naive_forecast(
                history,
                max_horizon,
            )

        else:
            raise ValueError(
                f"Unknown model: {model_name}"
            )

        for horizon in horizons:
            target = future.iloc[horizon - 1]

            rows.append(
                {
                    "timestamp": target["timestamp"],
                    "series": SERIES_NAME,
                    "horizon": int(horizon),
                    "actual": float(
                        target["request_count"]
                    ),
                    "prediction": float(
                        predictions[horizon - 1]
                    ),
                    "model": model_name,
                    "run_id": run_id,
                    "origin": origin,
                }
            )

        if (
            origin_index % 10 == 0
            or origin_index == len(origins)
        ):
            print(
                f"      evaluated "
                f"{origin_index}/{len(origins)} origins",
                flush=True,
            )

    return pd.DataFrame(rows)


# ============================================================
# EXTERNAL METRICS
# ============================================================

def calculate_external_metrics(
    predictions: pd.DataFrame,
) -> pd.DataFrame:

    if predictions.empty:
        raise ValueError(
            "No predictions available."
        )

    rows = []

    group_columns = [
        "model",
        "series",
        "horizon",
    ]

    for (
        model_name,
        series,
        horizon,
    ), group in predictions.groupby(
        group_columns
    ):

        actual = group["actual"].to_numpy(
            dtype=float
        )

        prediction = group["prediction"].to_numpy(
            dtype=float
        )

        errors = actual - prediction

        mae = float(
            np.mean(np.abs(errors))
        )

        rmse = float(
            np.sqrt(np.mean(errors ** 2))
        )

        denominator = (
            np.abs(actual)
            + np.abs(prediction)
        )

        numerator = (
            2.0
            * np.abs(actual - prediction)
        )

        valid = denominator != 0

        if np.any(valid):
            smape_value = float(
                np.mean(
                    numerator[valid]
                    / denominator[valid]
                )
                * 100.0
            )
        else:
            smape_value = 0.0

        rows.append(
            {
                "model": model_name,
                "series": series,
                "horizon": int(horizon),
                "MAE": mae,
                "RMSE": rmse,
                "sMAPE": smape_value,
                "n_predictions": len(group),
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "model",
                "series",
                "horizon",
            ]
        )
        .reset_index(drop=True)
    )


# ============================================================
# RF VALIDATION CONFIGURATION
# ============================================================

def select_rf_configuration(
    train: pd.DataFrame,
    validation: pd.DataFrame,
) -> tuple[dict, pd.DataFrame]:

    print(
        "\nSelecting RF configuration "
        "using validation only...",
        flush=True,
    )

    full_validation_data = pd.concat(
        [
            train,
            validation,
        ],
        ignore_index=True,
    )

    validation_origins = (
        validation["timestamp"]
        .sort_values()
        .tolist()
    )

    selection_rows = []

    for config_index, params in enumerate(
        RF_GRID,
        start=1,
    ):

        print(
            f"\n  [{config_index}/{len(RF_GRID)}] "
            f"Testing RF: "
            f"n_estimators={params['n_estimators']}, "
            f"min_samples_leaf="
            f"{params['min_samples_leaf']}, "
            f"max_depth={params['max_depth']}",
            flush=True,
        )

        model = fit_rf(
            train,
            params,
        )

        predictions = evaluate_external_model(
            model_name="RF",
            model=model,
            full_data=full_validation_data,
            origins=validation_origins,
            horizons=HORIZONS,
            run_id="validation",
        )

        metrics = calculate_external_metrics(
            predictions
        )

        selection_rows.append(
            {
                "config_index": config_index,
                "n_estimators": params[
                    "n_estimators"
                ],
                "min_samples_leaf": params[
                    "min_samples_leaf"
                ],
                "max_depth": params[
                    "max_depth"
                ],
                "mean_MAE": float(
                    metrics["MAE"].mean()
                ),
                "mean_RMSE": float(
                    metrics["RMSE"].mean()
                ),
                "mean_sMAPE": float(
                    metrics["sMAPE"].mean()
                ),
            }
        )

    selection_scores = (
        pd.DataFrame(selection_rows)
        .sort_values("mean_MAE")
        .reset_index(drop=True)
    )

    best_row = selection_scores.iloc[0]

    best_config = {
        "n_estimators": int(
            best_row["n_estimators"]
        ),
        "min_samples_leaf": int(
            best_row["min_samples_leaf"]
        ),
        "max_depth": (
            None
            if pd.isna(best_row["max_depth"])
            else int(best_row["max_depth"])
        ),
    }

    print("\nBest RF configuration:")
    print(json.dumps(best_config, indent=2))
    print(
        f"Validation mean MAE: "
        f"{best_row['mean_MAE']:.4f}"
    )

    return best_config, selection_scores


# ============================================================
# MAIN EXPERIMENT
# ============================================================

def main() -> None:

    data = load_external_series()

    train, validation, test = (
        chronological_split_external(data)
    )

    verify_external_split(
        train,
        validation,
        test,
    )

    run_id = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    run_dir = (
        RESULTS_ROOT
        / run_id
        / "dataset_b_gentd26"
    )

    metrics_dir = run_dir / "metrics"
    predictions_dir = run_dir / "predictions"
    metadata_dir = run_dir / "metadata"

    metrics_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    predictions_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    metadata_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        f"\nRun ID: {run_id}"
    )

    # --------------------------------------------------------
    # Validation-only RF selection
    # --------------------------------------------------------

    best_config, selection_scores = (
        select_rf_configuration(
            train,
            validation,
        )
    )

    selection_scores.to_csv(
        metrics_dir
        / "rf_validation_selection.csv",
        index=False,
    )

    # --------------------------------------------------------
    # Final training data
    # --------------------------------------------------------

    train_validation = pd.concat(
        [
            train,
            validation,
        ],
        ignore_index=True,
    )

    rf_model = fit_rf(
        train_validation,
        best_config,
    )

    test_origins = (
        test["timestamp"]
        .sort_values()
        .tolist()
    )

    full_test_data = pd.concat(
        [
            train_validation,
            test,
        ],
        ignore_index=True,
    )

    all_predictions = []

    # RF
    rf_predictions = evaluate_external_model(
        model_name="RF",
        model=rf_model,
        full_data=full_test_data,
        origins=test_origins,
        horizons=HORIZONS,
        run_id=run_id,
    )

    all_predictions.append(rf_predictions)

    # Persistence
    persistence_predictions = (
        evaluate_external_model(
            model_name="Persistence",
            model=None,
            full_data=full_test_data,
            origins=test_origins,
            horizons=HORIZONS,
            run_id=run_id,
        )
    )

    all_predictions.append(
        persistence_predictions
    )

    # Seasonal naive
    seasonal_predictions = (
        evaluate_external_model(
            model_name="SeasonalNaive",
            model=None,
            full_data=full_test_data,
            origins=test_origins,
            horizons=HORIZONS,
            run_id=run_id,
        )
    )

    all_predictions.append(
        seasonal_predictions
    )

    predictions = pd.concat(
        all_predictions,
        ignore_index=True,
    )

    metrics = calculate_external_metrics(
        predictions
    )

    predictions.to_csv(
        predictions_dir
        / "test_predictions.csv",
        index=False,
    )

    metrics.to_csv(
        metrics_dir
        / "test_metrics.csv",
        index=False,
    )

    metadata = {
        "run_id": run_id,
        "dataset": "GenTD26",
        "series": SERIES_NAME,
        "data_path": str(DATA_PATH),
        "input_sha256": sha256_file(DATA_PATH),
        "git_commit": get_git_commit(),
        "created_at_utc": utc_now_iso(),
        "random_state": RANDOM_STATE,
        "horizons": HORIZONS,
        "feature_columns": FEATURE_COLUMNS,
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
            "The raw request-arrival timestamps were aggregated into "
            "hourly request counts by flooring `gmt_create` to the hour. "
            "Missing hours within the observed range were represented "
            "as zero requests.",
            "RF is selected using validation only.",
            "Test observations are not used for model fitting.",
            "Test observations are used as rolling history.",
        ],
    }

    with (
        metadata_dir / "run_metadata.json"
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

    print("\nExternal forecasting complete.")
    print(f"Results directory: {run_dir}")
    print("\nTest metrics:")
    print(metrics.to_string(index=False))


if __name__ == "__main__":
    main()