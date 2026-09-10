from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

ORIGINAL_RUN = Path("results/20260910T174657Z")
ABLATION_RUN = Path("results/20260910T175101Z")

OUTPUT_DIR = Path(
    "results/forecast_analysis"
)


# ============================================================
# HELPERS
# ============================================================


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    return pd.read_csv(path)


def print_section(title: str) -> None:
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


# ============================================================
# MAIN ANALYSIS
# ============================================================


def main() -> None:

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print_section(
        "Forecast Error Analysis"
    )

    print(
        f"Original run: {ORIGINAL_RUN}"
    )

    print(
        f"Ablation run: {ABLATION_RUN}"
    )

    # --------------------------------------------------------
    # LOAD ORIGINAL RESULTS
    # --------------------------------------------------------

    metrics = load_csv(
        ORIGINAL_RUN / "metrics.csv"
    )

    predictions = load_csv(
        ORIGINAL_RUN / "predictions.csv"
    )

    ablation = load_csv(
        ABLATION_RUN / "ablation_comparison.csv"
    )

    predictions["timestamp"] = pd.to_datetime(
        predictions["timestamp"],
        utc=True,
    )

    predictions["origin"] = pd.to_datetime(
        predictions["origin"],
        utc=True,
    )

    # --------------------------------------------------------
    # 1. AGGREGATE MAE BY MODEL AND HORIZON
    # --------------------------------------------------------

    print_section(
        "1. Aggregate MAE by Model and Horizon"
    )

    aggregate_mae = (
        metrics.groupby(
            ["model", "horizon"],
            as_index=False,
        )["MAE"]
        .mean()
        .sort_values(
            ["horizon", "MAE"]
        )
    )

    print(
        aggregate_mae.to_string(
            index=False
        )
    )

    aggregate_mae.to_csv(
        OUTPUT_DIR
        / "aggregate_mae_by_horizon.csv",
        index=False,
    )

    # --------------------------------------------------------
    # 2. RF IMPROVEMENT VS BASELINES
    # --------------------------------------------------------

    print_section(
        "2. RF Improvement vs Baselines"
    )

    pivot = (
        aggregate_mae
        .pivot(
            index="horizon",
            columns="model",
            values="MAE",
        )
        .reset_index()
    )

    pivot["RF_vs_Persistence_percent"] = (
        (
            pivot["RF"]
            - pivot["Persistence"]
        )
        / pivot["Persistence"]
        * 100.0
    )

    pivot["RF_vs_SeasonalNaive_percent"] = (
        (
            pivot["RF"]
            - pivot["SeasonalNaive"]
        )
        / pivot["SeasonalNaive"]
        * 100.0
    )

    print(
        pivot.to_string(
            index=False
        )
    )

    pivot.to_csv(
        OUTPUT_DIR
        / "rf_vs_baselines.csv",
        index=False,
    )

    # --------------------------------------------------------
    # 3. ENDPOINT × HORIZON RF PERFORMANCE
    # --------------------------------------------------------

    print_section(
        "3. RF MAE by Endpoint and Horizon"
    )

    rf_metrics = metrics[
        metrics["model"] == "RF"
    ].copy()

    rf_endpoint = (
        rf_metrics
        .pivot(
            index="endpoint",
            columns="horizon",
            values="MAE",
        )
        .reset_index()
    )

    rf_endpoint.columns.name = None

    print(
        rf_endpoint.to_string(
            index=False
        )
    )

    rf_endpoint.to_csv(
        OUTPUT_DIR
        / "rf_mae_endpoint_horizon.csv",
        index=False,
    )

    # --------------------------------------------------------
    # 4. WHERE DOES RF LOSE TO PERSISTENCE?
    # --------------------------------------------------------

    print_section(
        "4. RF vs Persistence by Endpoint and Horizon"
    )

    comparison = (
        metrics[
            metrics["model"].isin(
                ["RF", "Persistence"]
            )
        ]
        .pivot(
            index=[
                "endpoint",
                "horizon",
            ],
            columns="model",
            values="MAE",
        )
        .reset_index()
    )

    comparison.columns.name = None

    comparison["RF_minus_Persistence_MAE"] = (
        comparison["RF"]
        - comparison["Persistence"]
    )

    comparison["RF_percent_vs_Persistence"] = (
        (
            comparison["RF"]
            - comparison["Persistence"]
        )
        / comparison["Persistence"]
        * 100.0
    )

    comparison["RF_wins"] = (
        comparison["RF"]
        < comparison["Persistence"]
    )

    print(
        comparison.to_string(
            index=False
        )
    )

    comparison.to_csv(
        OUTPUT_DIR
        / "rf_vs_persistence_by_endpoint.csv",
        index=False,
    )

    print(
        "\nCases where RF loses to persistence:"
    )

    losses = comparison[
        comparison["RF_wins"] == False
    ]

    print(
        losses.to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # 5. WORST RF FORECASTS
    # --------------------------------------------------------

    print_section(
        "5. Worst Individual RF Forecasts"
    )

    rf_predictions = predictions[
        predictions["model"] == "RF"
    ].copy()

    rf_predictions["error"] = (
        rf_predictions["actual"]
        - rf_predictions["prediction"]
    )

    rf_predictions["absolute_error"] = (
        np.abs(
            rf_predictions["error"]
        )
    )

    rf_predictions["absolute_percentage_error"] = np.where(
        rf_predictions["actual"] != 0,
        (
            rf_predictions["absolute_error"]
            / np.abs(
                rf_predictions["actual"]
            )
            * 100.0
        ),
        np.nan,
    )

    worst = (
        rf_predictions
        .sort_values(
            "absolute_error",
            ascending=False,
        )
        .head(20)
    )

    print(
        worst[
            [
                "timestamp",
                "origin",
                "endpoint",
                "horizon",
                "actual",
                "prediction",
                "error",
                "absolute_error",
                "absolute_percentage_error",
            ]
        ].to_string(
            index=False
        )
    )

    worst.to_csv(
        OUTPUT_DIR
        / "worst_rf_forecasts.csv",
        index=False,
    )

    # --------------------------------------------------------
    # 6. RF ERROR BY ENDPOINT
    # --------------------------------------------------------

    print_section(
        "6. RF Error by Endpoint"
    )

    endpoint_error = (
        rf_predictions
        .groupby(
            "endpoint",
            as_index=False,
        )
        .agg(
            MAE=(
                "absolute_error",
                "mean",
            ),
            RMSE=(
                "error",
                lambda x: np.sqrt(
                    np.mean(
                        x ** 2
                    )
                ),
            ),
            Mean_Error=(
                "error",
                "mean",
            ),
            Max_Absolute_Error=(
                "absolute_error",
                "max",
            ),
            N=(
                "error",
                "count",
            ),
        )
        .sort_values(
            "MAE",
            ascending=False,
        )
    )

    print(
        endpoint_error.to_string(
            index=False
        )
    )

    endpoint_error.to_csv(
        OUTPUT_DIR
        / "rf_error_by_endpoint.csv",
        index=False,
    )

    # --------------------------------------------------------
    # 7. RF ERROR BY HORIZON
    # --------------------------------------------------------

    print_section(
        "7. RF Error by Horizon"
    )

    horizon_error = (
        rf_predictions
        .groupby(
            "horizon",
            as_index=False,
        )
        .agg(
            MAE=(
                "absolute_error",
                "mean",
            ),
            RMSE=(
                "error",
                lambda x: np.sqrt(
                    np.mean(
                        x ** 2
                    )
                ),
            ),
            Mean_Error=(
                "error",
                "mean",
            ),
            Max_Absolute_Error=(
                "absolute_error",
                "max",
            ),
            N=(
                "error",
                "count",
            ),
        )
        .sort_values(
            "horizon"
        )
    )

    print(
        horizon_error.to_string(
            index=False
        )
    )

    horizon_error.to_csv(
        OUTPUT_DIR
        / "rf_error_by_horizon.csv",
        index=False,
    )

    # --------------------------------------------------------
    # 8. ERROR OVER TIME
    # --------------------------------------------------------

    print_section(
        "8. RF Error Over Time"
    )

    time_error = (
        rf_predictions
        .groupby(
            [
                "timestamp",
                "horizon",
            ],
            as_index=False,
        )
        .agg(
            MAE=(
                "absolute_error",
                "mean",
            ),
            Mean_Error=(
                "error",
                "mean",
            ),
        )
    )

    time_error.to_csv(
        OUTPUT_DIR
        / "rf_error_over_time.csv",
        index=False,
    )

    print(
        time_error.head(20).to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # 9. PAYMENTS FAILURE ANALYSIS
    # --------------------------------------------------------

    print_section(
        "9. /payments Error Analysis"
    )

    payments = rf_predictions[
        rf_predictions["endpoint"]
        == "/payments"
    ].copy()

    payments_summary = (
        payments
        .groupby(
            "horizon",
            as_index=False,
        )
        .agg(
            MAE=(
                "absolute_error",
                "mean",
            ),
            RMSE=(
                "error",
                lambda x: np.sqrt(
                    np.mean(
                        x ** 2
                    )
                ),
            ),
            Mean_Error=(
                "error",
                "mean",
            ),
            Max_Absolute_Error=(
                "absolute_error",
                "max",
            ),
        )
    )

    print(
        payments_summary.to_string(
            index=False
        )
    )

    payments_summary.to_csv(
        OUTPUT_DIR
        / "payments_error_summary.csv",
        index=False,
    )

    # --------------------------------------------------------
    # 10. ABLATION SUMMARY
    # --------------------------------------------------------

    print_section(
        "10. lag_24 Ablation Summary"
    )

    ablation_summary = (
        ablation
        .groupby(
            "horizon",
            as_index=False,
        )
        .agg(
            Mean_MAE_Full=(
                "MAE_RF_FullFeatures",
                "mean",
            ),
            Mean_MAE_WithoutLag24=(
                "MAE_RF_WithoutLag24",
                "mean",
            ),
            Mean_MAE_Change=(
                "MAE_change_without_lag24",
                "mean",
            ),
            Mean_MAE_Percent_Change=(
                "MAE_percent_change_without_lag24",
                "mean",
            ),
        )
    )

    print(
        ablation_summary.to_string(
            index=False
        )
    )

    ablation_summary.to_csv(
        OUTPUT_DIR
        / "lag24_ablation_summary.csv",
        index=False,
    )

    # --------------------------------------------------------
    # 11. ABLATION WIN COUNT
    # --------------------------------------------------------

    print_section(
        "11. lag_24 Ablation Win Count"
    )

    ablation["without_lag24_better"] = (
        ablation[
            "MAE_RF_WithoutLag24"
        ]
        <
        ablation[
            "MAE_RF_FullFeatures"
        ]
    )

    win_count = (
        ablation[
            "without_lag24_better"
        ]
        .value_counts()
        .rename_axis(
            "without_lag24_better"
        )
        .reset_index(
            name="count"
        )
    )

    print(
        win_count.to_string(
            index=False
        )
    )

    print(
        f"\nWithout lag_24 better in "
        f"{ablation['without_lag24_better'].sum()}"
        f"/{len(ablation)} endpoint-horizon cases."
    )

    # --------------------------------------------------------
    # 12. OVERALL SUMMARY
    # --------------------------------------------------------

    print_section(
        "12. Key Summary"
    )

    print(
        "Number of RF prediction rows:",
        len(rf_predictions),
    )

    print(
        "Endpoints:",
        sorted(
            rf_predictions["endpoint"]
            .unique()
            .tolist()
        ),
    )

    print(
        "Horizons:",
        sorted(
            rf_predictions["horizon"]
            .unique()
            .tolist()
        ),
    )

    print(
        "\nAggregate RF MAE:"
    )

    print(
        rf_predictions[
            "absolute_error"
        ].mean()
    )

    print(
        "\nAnalysis files saved to:"
    )

    print(
        OUTPUT_DIR
    )

    print_section(
        "Analysis Complete"
    )


if __name__ == "__main__":
    main()