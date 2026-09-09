from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

ANALYSIS_DIR = Path(
    "results/forecast_analysis"
)

OUTPUT_DIR = Path(
    "results/forecast_analysis/figures"
)

DPI = 300


# ============================================================
# HELPERS
# ============================================================


def save_figure(
    fig: plt.Figure,
    filename: str,
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = OUTPUT_DIR / filename

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=DPI,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(f"Saved: {path}")


# ============================================================
# FIGURE 1
# RF VS BASELINES BY HORIZON
# ============================================================


def figure_1_mae_by_horizon() -> None:

    data = pd.read_csv(
        ANALYSIS_DIR
        / "aggregate_mae_by_horizon.csv"
    )

    pivot = data.pivot(
        index="horizon",
        columns="model",
        values="MAE",
    )

    horizons = pivot.index.tolist()

    fig, ax = plt.subplots(
        figsize=(8, 5)
    )

    for model in [
        "RF",
        "Persistence",
        "SeasonalNaive",
    ]:
        ax.plot(
            horizons,
            pivot[model],
            marker="o",
            linewidth=2,
            label=model,
        )

    ax.set_xlabel(
        "Forecast Horizon (hours)"
    )

    ax.set_ylabel(
        "Mean Absolute Error (MAE)"
    )

    ax.set_title(
        "Forecasting Performance by Horizon"
    )

    ax.set_xticks(
        horizons
    )

    ax.legend()

    ax.grid(
        axis="y",
        alpha=0.25,
    )

    save_figure(
        fig,
        "figure_1_mae_by_horizon.png",
    )


# ============================================================
# FIGURE 2
# RF MAE BY ENDPOINT AND HORIZON
# ============================================================


def figure_2_endpoint_horizon() -> None:

    data = pd.read_csv(
        ANALYSIS_DIR
        / "rf_mae_endpoint_horizon.csv"
    )

    data = data.set_index(
        "endpoint"
    )

    horizons = [
        column
        for column in data.columns
        if str(column) in {
            "1",
            "6",
            "12",
        }
    ]

    fig, ax = plt.subplots(
        figsize=(10, 5.5)
    )

    x = range(
        len(data.index)
    )

    width = 0.24

    offsets = [
        -width,
        0,
        width,
    ]

    for offset, horizon in zip(
        offsets,
        horizons,
    ):
        ax.bar(
            [
                value + offset
                for value in x
            ],
            data[horizon],
            width=width,
            label=f"{horizon}h",
        )

    ax.set_xlabel(
        "API Endpoint"
    )

    ax.set_ylabel(
        "Mean Absolute Error (MAE)"
    )

    ax.set_title(
        "RF Forecasting Error by Endpoint and Horizon"
    )

    ax.set_xticks(
        list(x)
    )

    ax.set_xticklabels(
        data.index
    )

    ax.legend(
        title="Horizon"
    )

    ax.grid(
        axis="y",
        alpha=0.25,
    )

    save_figure(
        fig,
        "figure_2_rf_mae_endpoint_horizon.png",
    )


# ============================================================
# FIGURE 3
# RF ERROR OVER TIME
# ============================================================


def figure_3_error_over_time() -> None:

    data = pd.read_csv(
        ANALYSIS_DIR
        / "rf_error_over_time.csv"
    )

    data["timestamp"] = pd.to_datetime(
        data["timestamp"],
        utc=True,
    )

    fig, ax = plt.subplots(
        figsize=(10, 5.5)
    )

    for horizon in [
        1,
        6,
        12,
    ]:

        subset = data[
            data["horizon"] == horizon
        ].copy()

        # Smooth visualization while preserving
        # the underlying hourly evaluation.
        subset = (
            subset
            .set_index("timestamp")
            ["MAE"]
            .rolling(
                window=6,
                min_periods=1,
            )
            .mean()
        )

        ax.plot(
            subset.index,
            subset.values,
            linewidth=2,
            label=f"{horizon}h",
        )

    ax.set_xlabel(
        "Timestamp (UTC)"
    )

    ax.set_ylabel(
        "Rolling Mean Absolute Error"
    )

    ax.set_title(
        "RF Forecast Error Over the Test Period"
    )

    ax.legend(
        title="Forecast Horizon"
    )

    ax.grid(
        axis="y",
        alpha=0.25,
    )

    fig.autofmt_xdate()

    save_figure(
        fig,
        "figure_3_rf_error_over_time.png",
    )


# ============================================================
# FIGURE 4
# LAG-24 ABLATION
# ============================================================


def figure_4_lag24_ablation() -> None:

    data = pd.read_csv(
        ANALYSIS_DIR
        / "lag24_ablation_summary.csv"
    )

    horizons = data[
        "horizon"
    ].tolist()

    fig, ax = plt.subplots(
        figsize=(8, 5)
    )

    ax.plot(
        horizons,
        data["Mean_MAE_Full"],
        marker="o",
        linewidth=2,
        label="Full feature set",
    )

    ax.plot(
        horizons,
        data["Mean_MAE_WithoutLag24"],
        marker="o",
        linewidth=2,
        label="Without lag_24",
    )

    ax.set_xlabel(
        "Forecast Horizon (hours)"
    )

    ax.set_ylabel(
        "Mean Absolute Error (MAE)"
    )

    ax.set_title(
        "Effect of Removing the 24-Hour Lag Feature"
    )

    ax.set_xticks(
        horizons
    )

    ax.legend()

    ax.grid(
        axis="y",
        alpha=0.25,
    )

    save_figure(
        fig,
        "figure_4_lag24_ablation.png",
    )


# ============================================================
# MAIN
# ============================================================


def main() -> None:

    print("=" * 60)
    print(
        "Generating Corrected Forecasting Figures"
    )
    print("=" * 60)

    print(
        f"Input directory: {ANALYSIS_DIR}"
    )

    print(
        f"Output directory: {OUTPUT_DIR}"
    )

    figure_1_mae_by_horizon()

    figure_2_endpoint_horizon()

    figure_3_error_over_time()

    figure_4_lag24_ablation()

    print()
    print("=" * 60)
    print(
        "Figure generation complete."
    )
    print("=" * 60)


if __name__ == "__main__":
    main()