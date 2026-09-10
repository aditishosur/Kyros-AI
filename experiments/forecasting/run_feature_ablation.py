from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from experiments.forecasting.temporal_split import (
    chronological_split,
    verify_split,
)


# ============================================================
# CONFIGURATION
# ============================================================

DATA_PATH = Path("data/api_logs.csv")
RESULTS_ROOT = Path("results")

HORIZONS = [1, 6, 12]

RANDOM_STATE = 42

# ------------------------------------------------------------
# FROZEN RF CONFIGURATION
# ------------------------------------------------------------
#
# This is the configuration selected during the original
# validation-only experiment.
#
# IMPORTANT:
# No hyperparameter selection is performed in this ablation.
# The purpose of this experiment is ONLY to measure the
# contribution of lag_24.
#
FROZEN_RF_CONFIG = {
    "n_estimators": 200,
    "min_samples_leaf": 2,
    "max_depth": None,
}


# ------------------------------------------------------------
# FEATURE SETS
# ------------------------------------------------------------

FULL_FEATURE_COLUMNS = [
    "hour",
    "day_of_week",
    "lag_1",
    "lag_3",
    "lag_6",
    "lag_24",
    "rolling_mean_6",
    "rolling_mean_24",
]

ABLATION_FEATURE_COLUMNS = [
    "hour",
    "day_of_week",
    "lag_1",
    "lag_3",
    "lag_6",
    "rolling_mean_6",
    "rolling_mean_24",
]


# ============================================================
# REPRODUCIBILITY HELPERS
# ============================================================


def sha256_file(path: Path) -> str:
    """
    Return SHA-256 hash of a file.
    """

    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            sha256.update(chunk)

    return sha256.hexdigest()


def get_git_commit() -> str:
    """
    Return current Git commit hash.

    If Git information is unavailable, return 'unknown'.
    """

    try:
        result = subprocess.run(
            [
                "git",
                "rev-parse",
                "HEAD",
            ],
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
    """
    Return current UTC timestamp in ISO-8601 format.
    """

    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# DATA PREPARATION
# ============================================================


def make_hourly(endpoint_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert one endpoint's observations into an hourly time series.
    """

    data = endpoint_df.copy()

    data["timestamp"] = pd.to_datetime(
        data["timestamp"],
        utc=True,
    )

    data = (
        data.sort_values("timestamp")
        .drop_duplicates(
            subset=["timestamp"],
            keep="first",
        )
    )

    hourly = (
        data.set_index("timestamp")["request_count"]
        .resample("1h")
        .sum()
        .rename("request_count")
        .reset_index()
    )

    return hourly


def make_features(history: pd.DataFrame) -> pd.DataFrame:
    """
    Construct all forecasting features.

    Feature construction itself remains identical to the
    original forecasting experiment.

    The ablation is performed later by selecting either the
    full feature list or the list without lag_24.
    """

    data = history.copy()

    data["timestamp"] = pd.to_datetime(
        data["timestamp"],
        utc=True,
    )

    data = (
        data.sort_values("timestamp")
        .reset_index(drop=True)
    )

    data["hour"] = data["timestamp"].dt.hour

    data["day_of_week"] = (
        data["timestamp"].dt.dayofweek
    )

    data["lag_1"] = (
        data["request_count"].shift(1)
    )

    data["lag_3"] = (
        data["request_count"].shift(3)
    )

    data["lag_6"] = (
        data["request_count"].shift(6)
    )

    data["lag_24"] = (
        data["request_count"].shift(24)
    )

    # Shift before rolling so the current observation is
    # never included in its own forecasting features.
    data["rolling_mean_6"] = (
        data["request_count"]
        .shift(1)
        .rolling(6)
        .mean()
    )

    data["rolling_mean_24"] = (
        data["request_count"]
        .shift(1)
        .rolling(24)
        .mean()
    )

    return data


# ============================================================
# RANDOM FOREST
# ============================================================


def fit_rf(
    history: pd.DataFrame,
    feature_columns: list[str],
) -> RandomForestRegressor:
    """
    Fit the frozen Random Forest configuration using the
    requested feature set.

    No hyperparameter tuning occurs here.
    """

    features = make_features(history)

    features = features.dropna(
        subset=feature_columns + ["request_count"]
    )

    if features.empty:
        raise ValueError(
            "No valid training rows remain after feature construction."
        )

    model = RandomForestRegressor(
        n_estimators=FROZEN_RF_CONFIG["n_estimators"],
        min_samples_leaf=FROZEN_RF_CONFIG["min_samples_leaf"],
        max_depth=FROZEN_RF_CONFIG["max_depth"],
        random_state=RANDOM_STATE,
        n_jobs=1,
    )

    model.fit(
        features[feature_columns],
        features["request_count"],
    )

    return model


def recursive_rf_forecast(
    model: RandomForestRegressor,
    history: pd.DataFrame,
    horizon: int,
    feature_columns: list[str],
) -> list[float]:
    """
    Generate recursive multi-step forecasts.

    Each prediction uses a feature row whose timestamp matches
    the timestamp being predicted. Features are constructed using
    only observations available before that prediction timestamp.

    Generated predictions are appended to the working history,
    so future forecast steps do not use future actual values.
    """

    if horizon < 1:
        raise ValueError(
            "horizon must be >= 1"
        )

    working = history[
        ["timestamp", "request_count"]
    ].copy()

    working["timestamp"] = pd.to_datetime(
        working["timestamp"],
        utc=True,
    )

    working = (
        working.sort_values("timestamp")
        .reset_index(drop=True)
    )

    predictions: list[float] = []

    for _ in range(horizon):

        next_timestamp = (
            working["timestamp"].iloc[-1]
            + pd.Timedelta(hours=1)
        )

        # Add a placeholder row for the timestamp being predicted.
        # All lag and rolling features are shifted, so the NaN
        # request_count is never used to predict itself.
        feature_history = pd.concat(
            [
                working,
                pd.DataFrame(
                    {
                        "timestamp": [next_timestamp],
                        "request_count": [np.nan],
                    }
                ),
            ],
            ignore_index=True,
        )

        feature_history = make_features(
            feature_history
        )

        # The final row now corresponds to next_timestamp.
        latest = feature_history.iloc[-1]

        x = pd.DataFrame(
            [
                {
                    column: latest[column]
                    for column in feature_columns
                }
            ]
        )

        if x.isna().any().any():
            raise ValueError(
                "Insufficient history to construct forecasting "
                "features for the next timestamp."
            )

        prediction = float(
            model.predict(x)[0]
        )

        predictions.append(prediction)

        # Append the generated prediction for the next
        # recursive forecasting step.
        working = pd.concat(
            [
                working,
                pd.DataFrame(
                    {
                        "timestamp": [next_timestamp],
                        "request_count": [prediction],
                    }
                ),
            ],
            ignore_index=True,
        )

    return predictions


# ============================================================
# ROLLING-ORIGIN EVALUATION
# ============================================================


def evaluate_rf(
    model_name: str,
    model: RandomForestRegressor,
    full_data: pd.DataFrame,
    origins: list[pd.Timestamp],
    horizons: list[int],
    endpoint: str,
    run_id: str,
    feature_columns: list[str],
) -> pd.DataFrame:
    """
    Evaluate one RF feature configuration using rolling origins.
    """

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

        predictions = recursive_rf_forecast(
            model=model,
            history=history,
            horizon=max_horizon,
            feature_columns=feature_columns,
        )

        for horizon in horizons:

            target = future.iloc[
                horizon - 1
            ]

            rows.append(
                {
                    "timestamp": target["timestamp"],
                    "endpoint": endpoint,
                    "horizon": horizon,
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
# METRICS
# ============================================================


def smape(
    actual: np.ndarray,
    prediction: np.ndarray,
) -> float:
    """
    Symmetric Mean Absolute Percentage Error.
    """

    denominator = (
        np.abs(actual)
        + np.abs(prediction)
    )

    numerator = (
        2.0
        * np.abs(actual - prediction)
    )

    valid = denominator != 0

    if not np.any(valid):
        return 0.0

    return float(
        np.mean(
            numerator[valid]
            / denominator[valid]
        )
        * 100.0
    )


def calculate_metrics(
    predictions: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate MAE, RMSE and sMAPE grouped by:

        model
        endpoint
        horizon
    """

    if predictions.empty:
        raise ValueError(
            "No predictions available for metric calculation."
        )

    rows = []

    group_columns = [
        "model",
        "endpoint",
        "horizon",
    ]

    for (
        model_name,
        endpoint,
        horizon,
    ), group in predictions.groupby(
        group_columns
    ):

        actual = (
            group["actual"]
            .to_numpy(dtype=float)
        )

        prediction = (
            group["prediction"]
            .to_numpy(dtype=float)
        )

        errors = (
            actual - prediction
        )

        mae = float(
            np.mean(
                np.abs(errors)
            )
        )

        rmse = float(
            np.sqrt(
                np.mean(
                    errors ** 2
                )
            )
        )

        smape_value = smape(
            actual,
            prediction,
        )

        rows.append(
            {
                "model": model_name,
                "endpoint": endpoint,
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
                "endpoint",
                "horizon",
            ]
        )
        .reset_index(drop=True)
    )


# ============================================================
# MAIN ABLATION EXPERIMENT
# ============================================================


def main() -> None:

    print(
        "============================================================"
    )
    print(
        "Forecasting Feature Ablation"
    )
    print(
        "============================================================"
    )

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    run_id = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    run_dir = (
        RESULTS_ROOT
        / run_id
    )

    run_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        f"Run ID: {run_id}",
        flush=True,
    )

    print(
        "\nAblation: full feature set vs. without lag_24",
        flush=True,
    )

    print(
        "No hyperparameter selection will be performed.",
        flush=True,
    )

    print(
        f"Frozen RF configuration: "
        f"{FROZEN_RF_CONFIG}",
        flush=True,
    )

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    print(
        "\nLoading dataset...",
        flush=True,
    )

    data = pd.read_csv(
        DATA_PATH
    )

    data["timestamp"] = pd.to_datetime(
        data["timestamp"],
        utc=True,
    )

    data = (
        data.sort_values(
            [
                "timestamp",
                "endpoint",
            ]
        )
        .reset_index(drop=True)
    )

    required_columns = {
        "timestamp",
        "endpoint",
        "request_count",
    }

    missing_columns = (
        required_columns
        - set(data.columns)
    )

    if missing_columns:
        raise ValueError(
            "Dataset is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    print(
        f"Loaded {len(data)} rows.",
        flush=True,
    )

    print(
        f"Unique timestamps: "
        f"{data['timestamp'].nunique()}",
        flush=True,
    )

    print(
        f"Endpoints: "
        f"{data['endpoint'].nunique()}",
        flush=True,
    )

    # --------------------------------------------------------
    # TEMPORAL SPLIT
    # --------------------------------------------------------

    split = chronological_split(
        data,
        train_fraction=0.60,
        validation_fraction=0.20,
    )

    verify_split(
        split
    )

    # --------------------------------------------------------
    # TRAIN + VALIDATION
    # --------------------------------------------------------

    train_validation = pd.concat(
        [
            split.train,
            split.validation,
        ],
        ignore_index=True,
    )

    endpoints = sorted(
        train_validation["endpoint"]
        .dropna()
        .unique()
        .tolist()
    )

    all_predictions = []

    # --------------------------------------------------------
    # TWO CONTROLLED FEATURE CONDITIONS
    # --------------------------------------------------------

    feature_conditions = [
        (
            "RF_FullFeatures",
            FULL_FEATURE_COLUMNS,
        ),
        (
            "RF_WithoutLag24",
            ABLATION_FEATURE_COLUMNS,
        ),
    ]

    for condition_name, feature_columns in feature_conditions:

        print(
            "\n============================================================",
            flush=True,
        )

        print(
            f"Condition: {condition_name}",
            flush=True,
        )

        print(
            f"Features: {feature_columns}",
            flush=True,
        )

        print(
            "============================================================",
            flush=True,
        )

        for endpoint_index, endpoint in enumerate(
            endpoints,
            start=1,
        ):

            print(
                f"\n  Endpoint "
                f"{endpoint_index}/{len(endpoints)}: "
                f"{endpoint}",
                flush=True,
            )

            train_validation_endpoint = (
                train_validation[
                    train_validation["endpoint"] == endpoint
                ][
                    ["timestamp", "request_count"]
                ].copy()
            )

            test_endpoint = (
                split.test[
                    split.test["endpoint"] == endpoint
                ][
                    ["timestamp", "request_count"]
                ].copy()
            )

            train_validation_hourly = make_hourly(
                train_validation_endpoint
            )

            test_hourly = make_hourly(
                test_endpoint
            )

            print(
                "    Fitting RF on train + validation...",
                flush=True,
            )

            model = fit_rf(
                train_validation_hourly,
                feature_columns,
            )

            full_test_data = pd.concat(
                [
                    train_validation_hourly,
                    test_hourly,
                ],
                ignore_index=True,
            )

            full_test_data = (
                full_test_data
                .sort_values("timestamp")
                .reset_index(drop=True)
            )

            origins = (
                test_hourly["timestamp"]
                .sort_values()
                .tolist()
            )

            print(
                "    Evaluating test set...",
                flush=True,
            )

            predictions = evaluate_rf(
                model_name=condition_name,
                model=model,
                full_data=full_test_data,
                origins=origins,
                horizons=HORIZONS,
                endpoint=endpoint,
                run_id=run_id,
                feature_columns=feature_columns,
            )

            if not predictions.empty:
                all_predictions.append(
                    predictions
                )

    # --------------------------------------------------------
    # COMBINE PREDICTIONS
    # --------------------------------------------------------

    if not all_predictions:
        raise RuntimeError(
            "No ablation predictions were generated."
        )

    predictions = pd.concat(
        all_predictions,
        ignore_index=True,
    )

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    metrics = calculate_metrics(
        predictions
    )

    predictions.to_csv(
        run_dir
        / "predictions.csv",
        index=False,
    )

    metrics.to_csv(
        run_dir
        / "metrics.csv",
        index=False,
    )

    # --------------------------------------------------------
    # DIRECT COMPARISON
    # --------------------------------------------------------

    comparison = metrics.pivot_table(
        index=[
            "endpoint",
            "horizon",
        ],
        columns="model",
        values=[
            "MAE",
            "RMSE",
            "sMAPE",
        ],
    )

    comparison.columns = [
        "_".join(
            [
                str(level)
                for level in column
            ]
        )
        for column in comparison.columns
    ]

    comparison = comparison.reset_index()

    if {
        "MAE_RF_FullFeatures",
        "MAE_RF_WithoutLag24",
    }.issubset(comparison.columns):

        comparison["MAE_change_without_lag24"] = (
            comparison["MAE_RF_WithoutLag24"]
            - comparison["MAE_RF_FullFeatures"]
        )

        comparison["MAE_percent_change_without_lag24"] = (
            (
                comparison["MAE_RF_WithoutLag24"]
                - comparison["MAE_RF_FullFeatures"]
            )
            / comparison["MAE_RF_FullFeatures"]
        ) * 100.0

    comparison.to_csv(
        run_dir
        / "ablation_comparison.csv",
        index=False,
    )

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    metadata = {
        "run_id": run_id,
        "created_at_utc": utc_now_iso(),
        "git_commit": get_git_commit(),
        "input_file": str(DATA_PATH),
        "input_sha256": sha256_file(
            DATA_PATH
        ),
        "random_state": RANDOM_STATE,
        "horizons": HORIZONS,
        "experiment": "feature_ablation",
        "ablation_feature": "lag_24",
        "full_features": FULL_FEATURE_COLUMNS,
        "ablated_features": ABLATION_FEATURE_COLUMNS,
        "frozen_rf_configuration": FROZEN_RF_CONFIG,
        "hyperparameter_selection_performed": False,
        "train_fraction": 0.60,
        "validation_fraction": 0.20,
        "test_fraction": 0.20,
        "train_timestamps": int(
            split.train["timestamp"].nunique()
        ),
        "validation_timestamps": int(
            split.validation["timestamp"].nunique()
        ),
        "test_timestamps": int(
            split.test["timestamp"].nunique()
        ),
        "train_rows": int(
            len(split.train)
        ),
        "validation_rows": int(
            len(split.validation)
        ),
        "test_rows": int(
            len(split.test)
        ),
        "evaluation_protocol": "rolling_origin",
        "rf_final_fit_data": "train_plus_validation",
        "test_used_for_selection": False,
        "purpose": (
            "Measure the contribution of lag_24 "
            "under the frozen forecasting protocol."
        ),
    }

    with (
        run_dir
        / "run_metadata.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=2,
        )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print(
        "\n============================================================"
    )

    print(
        "ABLATION RESULTS"
    )

    print(
        "============================================================"
    )

    print(
        metrics.to_string(
            index=False
        )
    )

    print(
        "\n------------------------------------------------------------"
    )

    print(
        "Direct comparison:",
        flush=True,
    )

    print(
        comparison.to_string(
            index=False
        ),
        flush=True,
    )

    print(
        "\n------------------------------------------------------------"
    )

    print(
        f"Results saved to: {run_dir}",
        flush=True,
    )

    print(
        "Files:",
        flush=True,
    )

    print(
        "  - metrics.csv",
        flush=True,
    )

    print(
        "  - predictions.csv",
        flush=True,
    )

    print(
        "  - ablation_comparison.csv",
        flush=True,
    )

    print(
        "  - run_metadata.json",
        flush=True,
    )

    print(
        "\nTest isolation: PASS",
        flush=True,
    )

    print(
        "No hyperparameter selection was performed.",
        flush=True,
    )

    print(
        "The same frozen RF configuration was used for both conditions.",
        flush=True,
    )

    print(
        "============================================================"
    )


if __name__ == "__main__":
    main()