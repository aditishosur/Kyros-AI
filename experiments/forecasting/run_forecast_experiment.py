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

FEATURE_COLUMNS = [
    "hour",
    "day_of_week",
    "lag_1",
    "lag_3",
    "lag_6",
    "lag_24",
    "rolling_mean_6",
    "rolling_mean_24",
]


# Small validation-only hyperparameter grid.
#
# IMPORTANT:
# This grid is used ONLY on train/validation.
# The test set is never used for configuration selection.
RF_GRID = [
    {
        "n_estimators": 100,
        "min_samples_leaf": 1,
        "max_depth": None,
    },
    {
        "n_estimators": 140,
        "min_samples_leaf": 2,
        "max_depth": None,
    },
    {
        "n_estimators": 200,
        "min_samples_leaf": 2,
        "max_depth": None,
    },
    {
        "n_estimators": 140,
        "min_samples_leaf": 4,
        "max_depth": None,
    },
    {
        "n_estimators": 140,
        "min_samples_leaf": 2,
        "max_depth": 10,
    },
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

    The dataset is already hourly, but this explicitly enforces
    the expected hourly representation.
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
    Construct forecasting features using only current/past observations.

    All lag and rolling features are shifted so that the current
    request_count is never used to predict itself.
    """

    data = history.copy()

    data["timestamp"] = pd.to_datetime(
        data["timestamp"],
        utc=True,
    )

    data = data.sort_values(
        "timestamp"
    ).reset_index(drop=True)

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

    # Shift first, then roll.
    #
    # This ensures that rolling features contain only
    # observations strictly before the prediction timestamp.
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
    params: dict,
) -> RandomForestRegressor:
    """
    Fit Random Forest on the supplied historical data.

    n_jobs=1 is intentional:
    it avoids unnecessary multiprocessing overhead and
    Windows process/thread behaviour during repeated
    rolling-origin evaluation.
    """

    features = make_features(history)

    features = features.dropna(
        subset=FEATURE_COLUMNS + ["request_count"]
    )

    if features.empty:
        raise ValueError(
            "No valid training rows remain after feature construction."
        )

    model = RandomForestRegressor(
        n_estimators=params["n_estimators"],
        min_samples_leaf=params["min_samples_leaf"],
        max_depth=params["max_depth"],
        random_state=RANDOM_STATE,
        n_jobs=1,
    )

    model.fit(
        features[FEATURE_COLUMNS],
        features["request_count"],
    )

    return model


def recursive_rf_forecast(
    model: RandomForestRegressor,
    history: pd.DataFrame,
    horizon: int,
) -> list[float]:
    """
    Generate recursive multi-step forecasts.

    After each prediction, the prediction is appended to the
    working history so later forecast steps use generated
    predictions rather than future actual values.
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

        # Build features from the information available
        # before the next prediction timestamp.
        feature_history = make_features(
            working
        )

        latest = feature_history.iloc[-1]

        x = pd.DataFrame(
            [
                {
                    column: latest[column]
                    for column in FEATURE_COLUMNS
                }
            ]
        )

        prediction = float(
            model.predict(x)[0]
        )

        predictions.append(prediction)

        # Append the generated prediction.
        working = pd.concat(
            [
                working,
                pd.DataFrame(
                    {
                        "timestamp": [
                            next_timestamp
                        ],
                        "request_count": [
                            prediction
                        ],
                    }
                ),
            ],
            ignore_index=True,
        )

    return predictions


# ============================================================
# BASELINES
# ============================================================


def persistence_forecast(
    history: pd.DataFrame,
    horizon: int,
) -> list[float]:
    """
    Persistence baseline:

        y(t+h) = y(t)

    for every forecast horizon h.
    """

    if history.empty:
        raise ValueError(
            "History is empty."
        )

    last_value = float(
        history["request_count"].iloc[-1]
    )

    return [
        last_value
        for _ in range(horizon)
    ]


def seasonal_naive_forecast(
    history: pd.DataFrame,
    horizon: int,
    season: int = 24,
) -> list[float]:
    """
    Seasonal-naive baseline for hourly data.

        y(t+h) = y(t+h-season)

    For this experiment season=24, corresponding to
    the same hour on the previous day.
    """

    if horizon < 1:
        raise ValueError(
            "horizon must be >= 1"
        )

    values = (
        history["request_count"]
        .astype(float)
        .tolist()
    )

    if len(values) < season:
        raise ValueError(
            f"Seasonal-naive forecast requires at least "
            f"{season} historical observations."
        )

    predictions: list[float] = []

    for step in range(1, horizon + 1):

        source_index = (
            len(values)
            - season
            + step
            - 1
        )

        if source_index >= len(values):
            raise AssertionError(
                "Seasonal-naive attempted to use "
                "future data."
            )

        predictions.append(
            float(values[source_index])
        )

    return predictions


# ============================================================
# ROLLING-ORIGIN EVALUATION
# ============================================================


def evaluate_model(
    model_name: str,
    model,
    full_data: pd.DataFrame,
    origins: list[pd.Timestamp],
    horizons: list[int],
    endpoint: str,
    run_id: str,
) -> pd.DataFrame:
    """
    Evaluate a forecasting method using rolling origins.

    At each origin:

        history = observations <= origin
        future  = observations > origin

    The model is NOT refit at every origin for RF.
    Instead, the already-fitted model is evaluated recursively
    using observations available up to each origin.

    One maximum-horizon forecast is generated per origin,
    and the requested horizons are extracted from it.
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

        # Progress every 10 origins.
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

    Returns percentage values.
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
# RF VALIDATION-ONLY CONFIGURATION SELECTION
# ============================================================


def select_rf_configuration(
    train_df: pd.DataFrame,
    validation_df: pd.DataFrame,
) -> tuple[dict, pd.DataFrame]:
    """
    Select the Random Forest configuration using validation only.

    Protocol:

        1. Fit each candidate configuration on TRAIN.
        2. Evaluate it on VALIDATION using rolling origins.
        3. Aggregate validation MAE across endpoints and horizons.
        4. Select the configuration with the lowest mean MAE.

    The TEST set is never accessed here.
    """

    print(
        "\nSelecting RF configuration using validation only...",
        flush=True,
    )

    endpoints = sorted(
        train_df["endpoint"]
        .dropna()
        .unique()
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
            f"min_samples_leaf={params['min_samples_leaf']}, "
            f"max_depth={params['max_depth']}",
            flush=True,
        )

        all_predictions = []

        for endpoint_index, endpoint in enumerate(
            endpoints,
            start=1,
        ):

            print(
                f"    Endpoint "
                f"{endpoint_index}/{len(endpoints)}: "
                f"{endpoint}",
                flush=True,
            )

            train_endpoint = train_df[
                train_df["endpoint"] == endpoint
            ][
                ["timestamp", "request_count"]
            ].copy()

            validation_endpoint = validation_df[
                validation_df["endpoint"] == endpoint
            ][
                ["timestamp", "request_count"]
            ].copy()

            train_hourly = make_hourly(
                train_endpoint
            )

            validation_hourly = make_hourly(
                validation_endpoint
            )

            # Fit ONLY on training data.
            model = fit_rf(
                train_hourly,
                params,
            )

            # For rolling-origin validation, the observed
            # validation values become available as history
            # as time progresses. They are NOT used to refit
            # the model.
            full_validation_data = pd.concat(
                [
                    train_hourly,
                    validation_hourly,
                ],
                ignore_index=True,
            )

            full_validation_data = (
                full_validation_data
                .sort_values("timestamp")
                .reset_index(drop=True)
            )

            origins = (
                validation_hourly["timestamp"]
                .sort_values()
                .tolist()
            )

            predictions = evaluate_model(
                model_name="RF",
                model=model,
                full_data=full_validation_data,
                origins=origins,
                horizons=HORIZONS,
                endpoint=endpoint,
                run_id="validation",
            )

            if not predictions.empty:
                all_predictions.append(
                    predictions
                )

        if not all_predictions:
            raise RuntimeError(
                "No validation predictions were generated."
            )

        validation_predictions = pd.concat(
            all_predictions,
            ignore_index=True,
        )

        validation_metrics = calculate_metrics(
            validation_predictions
        )

        mean_mae = float(
            validation_metrics["MAE"].mean()
        )

        mean_rmse = float(
            validation_metrics["RMSE"].mean()
        )

        mean_smape = float(
            validation_metrics["sMAPE"].mean()
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
                "mean_MAE": mean_mae,
                "mean_RMSE": mean_rmse,
                "mean_sMAPE": mean_smape,
            }
        )

        print(
            f"    Validation mean MAE: "
            f"{mean_mae:.4f}",
            flush=True,
        )

    selection_scores = (
        pd.DataFrame(selection_rows)
        .sort_values(
            "mean_MAE"
        )
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

    print(
        "\n  Best RF configuration selected:",
        flush=True,
    )
    print(
        f"    n_estimators={best_config['n_estimators']}",
        flush=True,
    )
    print(
        f"    min_samples_leaf="
        f"{best_config['min_samples_leaf']}",
        flush=True,
    )
    print(
        f"    max_depth={best_config['max_depth']}",
        flush=True,
    )
    print(
        f"    validation mean MAE="
        f"{best_row['mean_MAE']:.4f}",
        flush=True,
    )

    return (
        best_config,
        selection_scores,
    )


# ============================================================
# TEST EVALUATION
# ============================================================


def evaluate_test_set(
    train_validation_df: pd.DataFrame,
    test_df: pd.DataFrame,
    rf_config: dict,
    run_id: str,
) -> pd.DataFrame:
    """
    Perform final test evaluation.

    RF is refitted once using TRAIN + VALIDATION after
    hyperparameters have been frozen.

    Test observations are used only as rolling historical
    observations at prediction time. They are never used
    for model selection or refitting.
    """

    print(
        "\nPreparing final test evaluation...",
        flush=True,
    )

    endpoints = sorted(
        train_validation_df["endpoint"]
        .dropna()
        .unique()
        .tolist()
    )

    all_predictions = []

    for endpoint_index, endpoint in enumerate(
        endpoints,
        start=1,
    ):

        print(
            f"\n  Test endpoint "
            f"{endpoint_index}/{len(endpoints)}: "
            f"{endpoint}",
            flush=True,
        )

        train_validation_endpoint = (
            train_validation_df[
                train_validation_df["endpoint"] == endpoint
            ][
                ["timestamp", "request_count"]
            ].copy()
        )

        test_endpoint = (
            test_df[
                test_df["endpoint"] == endpoint
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

        # ----------------------------------------------------
        # FINAL RF FIT
        # ----------------------------------------------------

        print(
            "    Fitting final RF on "
            "train + validation...",
            flush=True,
        )

        model = fit_rf(
            train_validation_hourly,
            rf_config,
        )

        # ----------------------------------------------------
        # TEST DATA
        # ----------------------------------------------------

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

        # RF
        print(
            "    Evaluating RF...",
            flush=True,
        )

        rf_predictions = evaluate_model(
            model_name="RF",
            model=model,
            full_data=full_test_data,
            origins=origins,
            horizons=HORIZONS,
            endpoint=endpoint,
            run_id=run_id,
        )

        if not rf_predictions.empty:
            all_predictions.append(
                rf_predictions
            )

        # ----------------------------------------------------
        # PERSISTENCE
        # ----------------------------------------------------

        print(
            "    Evaluating Persistence...",
            flush=True,
        )

        persistence_predictions = evaluate_model(
            model_name="Persistence",
            model=None,
            full_data=full_test_data,
            origins=origins,
            horizons=HORIZONS,
            endpoint=endpoint,
            run_id=run_id,
        )

        if not persistence_predictions.empty:
            all_predictions.append(
                persistence_predictions
            )

        # ----------------------------------------------------
        # SEASONAL NAIVE
        # ----------------------------------------------------

        print(
            "    Evaluating Seasonal Naive...",
            flush=True,
        )

        seasonal_predictions = evaluate_model(
            model_name="SeasonalNaive",
            model=None,
            full_data=full_test_data,
            origins=origins,
            horizons=HORIZONS,
            endpoint=endpoint,
            run_id=run_id,
        )

        if not seasonal_predictions.empty:
            all_predictions.append(
                seasonal_predictions
            )

    if not all_predictions:
        raise RuntimeError(
            "No test predictions were generated."
        )

    return pd.concat(
        all_predictions,
        ignore_index=True,
    )


# ============================================================
# MAIN EXPERIMENT
# ============================================================


def main() -> None:

    # --------------------------------------------------------
    # BASIC SETUP
    # --------------------------------------------------------

    print(
        "============================================================"
    )
    print(
        "Forecasting Experiment"
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
    # VALIDATION-ONLY MODEL SELECTION
    # --------------------------------------------------------

    best_config, selection_scores = (
        select_rf_configuration(
            split.train,
            split.validation,
        )
    )

    selection_scores.to_csv(
        run_dir
        / "rf_validation_selection.csv",
        index=False,
    )

    with (
        run_dir
        / "frozen_config.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            {
                "model": "RandomForestRegressor",
                "selected_on": "validation_only",
                "config": best_config,
                "random_state": RANDOM_STATE,
                "features": FEATURE_COLUMNS,
                "horizons": HORIZONS,
            },
            file,
            indent=2,
        )

    print(
        "\nFrozen RF configuration saved.",
        flush=True,
    )

    # --------------------------------------------------------
    # FINAL TEST EVALUATION
    # --------------------------------------------------------

    train_validation = pd.concat(
        [
            split.train,
            split.validation,
        ],
        ignore_index=True,
    )

    test_predictions = evaluate_test_set(
        train_validation_df=train_validation,
        test_df=split.test,
        rf_config=best_config,
        run_id=run_id,
    )

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    metrics = calculate_metrics(
        test_predictions
    )

    test_predictions.to_csv(
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
    # RUN METADATA
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
        "features": FEATURE_COLUMNS,
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
        "rf_configuration": best_config,
        "selection_metric": "MAE",
        "selection_data": "train_validation_only",
        "test_used_for_selection": False,
        "rf_final_fit_data": "train_plus_validation",
        "evaluation_protocol": "rolling_origin",
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
        "TEST RESULTS"
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
        f"Results saved to: {run_dir}",
        flush=True,
    )

    print(
        "Files:",
        flush=True,
    )

    print(
        "  - rf_validation_selection.csv",
        flush=True,
    )

    print(
        "  - frozen_config.json",
        flush=True,
    )

    print(
        "  - predictions.csv",
        flush=True,
    )

    print(
        "  - metrics.csv",
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
        "Test data was not used for RF configuration selection.",
        flush=True,
    )

    print(
        "============================================================"
    )


if __name__ == "__main__":
    main()