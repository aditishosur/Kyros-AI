
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

RUN_ID = "20260917T145858Z"

BASE_DIR = Path(
    f"results/{RUN_ID}/dataset_b_gentd26"
)

METRICS_PATH = BASE_DIR / "metrics/test_metrics.csv"

PREDICTIONS_PATH = (
    BASE_DIR / "predictions/test_predictions.csv"
)

FIGURES_DIR = BASE_DIR / "figures"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# HELPERS
# ============================================================

def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    metrics = pd.read_csv(METRICS_PATH)

    predictions = pd.read_csv(PREDICTIONS_PATH)
    predictions["timestamp"] = pd.to_datetime(
        predictions["timestamp"]
    )

    predictions["error"] = (
        predictions["actual"] - predictions["prediction"]
    )

    predictions["abs_error"] = (
        predictions["error"].abs()
    )

    predictions["target_hour"] = (
        predictions["timestamp"].dt.hour
    )

    predictions["actual_zero"] = (
        predictions["actual"] == 0
    )

    return metrics, predictions


def save_figure(fig, filename: str) -> None:
    output_path = FIGURES_DIR / filename

    fig.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(f"Saved: {output_path}")


# ============================================================
# FIGURE 1: MAE BY HORIZON
# ============================================================

def plot_mae_by_horizon(
    metrics: pd.DataFrame,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))

    for model in metrics["model"].unique():
        model_data = metrics[
            metrics["model"] == model
        ].sort_values("horizon")

        ax.plot(
            model_data["horizon"],
            model_data["MAE"],
            marker="o",
            label=model,
        )

    ax.set_xticks([1, 6, 12])
    ax.set_xlabel("Forecast horizon (hours)")
    ax.set_ylabel("MAE")
    ax.set_title(
        "GenTD26 Test MAE by Forecast Horizon"
    )
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.tight_layout()

    save_figure(
        fig,
        "test_mae_by_horizon.png",
    )


# ============================================================
# FIGURE 2: MAE AND RMSE COMPARISON
# ============================================================

def plot_metric_comparison(
    metrics: pd.DataFrame,
) -> None:
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(12, 5),
    )

    for ax, metric in zip(
        axes,
        ["MAE", "RMSE"],
    ):
        for model in metrics["model"].unique():
            model_data = metrics[
                metrics["model"] == model
            ].sort_values("horizon")

            ax.plot(
                model_data["horizon"],
                model_data[metric],
                marker="o",
                label=model,
            )

        ax.set_xticks([1, 6, 12])
        ax.set_xlabel("Forecast horizon (hours)")
        ax.set_ylabel(metric)
        ax.set_title(
            f"{metric} by Forecast Horizon"
        )
        ax.grid(True, alpha=0.3)

    axes[1].legend()

    fig.suptitle(
        "GenTD26 Test Error Comparison",
        fontsize=14,
    )

    fig.tight_layout()

    save_figure(
        fig,
        "test_mae_rmse_comparison.png",
    )


# ============================================================
# FIGURE 3: ACTUAL VS PREDICTED OVER TIME
# ============================================================

def plot_actual_vs_predicted(
    predictions: pd.DataFrame,
) -> None:
    models = predictions["model"].unique()
    horizons = sorted(
        predictions["horizon"].unique()
    )

    for horizon in horizons:
        fig, ax = plt.subplots(figsize=(12, 5))

        horizon_data = predictions[
            predictions["horizon"] == horizon
        ].sort_values("timestamp")

        actual_data = (
            horizon_data
            .drop_duplicates(subset=["timestamp"])
            .sort_values("timestamp")
        )

        ax.plot(
            actual_data["timestamp"],
            actual_data["actual"],
            label="Actual",
            linewidth=2,
        )

        for model in models:
            model_data = horizon_data[
                horizon_data["model"] == model
            ].sort_values("timestamp")

            ax.plot(
                model_data["timestamp"],
                model_data["prediction"],
                label=model,
                alpha=0.8,
            )

        ax.set_xlabel("Target timestamp")
        ax.set_ylabel("Request count")
        ax.set_title(
            f"GenTD26 Actual vs Predicted "
            f"({horizon}h Horizon)"
        )
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()

        fig.tight_layout()

        save_figure(
            fig,
            f"actual_vs_predicted_{horizon}h.png",
        )


# ============================================================
# FIGURE 4: ERROR BY HOUR OF DAY
# ============================================================

def plot_error_by_hour(
    predictions: pd.DataFrame,
) -> None:
    grouped = (
        predictions
        .groupby(
            ["model", "horizon", "target_hour"],
            as_index=False,
        )
        .agg(
            MAE=("abs_error", "mean"),
        )
    )

    horizons = sorted(
        grouped["horizon"].unique()
    )

    for horizon in horizons:
        fig, ax = plt.subplots(figsize=(10, 5))

        horizon_data = grouped[
            grouped["horizon"] == horizon
        ]

        for model in horizon_data["model"].unique():
            model_data = horizon_data[
                horizon_data["model"] == model
            ].sort_values("target_hour")

            ax.plot(
                model_data["target_hour"],
                model_data["MAE"],
                marker="o",
                label=model,
            )

        ax.set_xticks(range(24))
        ax.set_xlabel("Target hour of day")
        ax.set_ylabel("MAE")
        ax.set_title(
            f"GenTD26 MAE by Target Hour "
            f"({horizon}h Horizon)"
        )
        ax.legend()
        ax.grid(True, alpha=0.3)

        fig.tight_layout()

        save_figure(
            fig,
            f"error_by_hour_{horizon}h.png",
        )


# ============================================================
# FIGURE 5: ERROR BY ZERO VS NONZERO ACTUALS
# ============================================================

def plot_zero_vs_nonzero_error(
    predictions: pd.DataFrame,
) -> None:
    predictions = predictions.copy()

    predictions["actual_group"] = (
        predictions["actual_zero"]
        .map({
            True: "Zero actual",
            False: "Nonzero actual",
        })
    )

    grouped = (
        predictions
        .groupby(
            ["model", "horizon", "actual_group"],
            as_index=False,
        )
        .agg(
            MAE=("abs_error", "mean"),
        )
    )

    horizons = sorted(
        grouped["horizon"].unique()
    )

    for horizon in horizons:
        horizon_data = grouped[
            grouped["horizon"] == horizon
        ]

        pivot = horizon_data.pivot(
            index="model",
            columns="actual_group",
            values="MAE",
        )

        pivot = pivot.reindex(
            columns=[
                "Zero actual",
                "Nonzero actual",
            ]
        )

        ax = pivot.plot(
            kind="bar",
            figsize=(9, 5),
        )

        ax.set_xlabel("Model")
        ax.set_ylabel("MAE")
        ax.set_title(
            f"GenTD26 Error by Actual Demand Group "
            f"({horizon}h Horizon)"
        )
        ax.legend(title="Actual group")
        ax.grid(
            axis="y",
            alpha=0.3,
        )

        fig = ax.get_figure()
        fig.tight_layout()

        save_figure(
            fig,
            f"error_zero_vs_nonzero_{horizon}h.png",
        )


# ============================================================
# FIGURE 6: RESIDUAL DISTRIBUTION
# ============================================================

def plot_residual_distribution(
    predictions: pd.DataFrame,
) -> None:
    models = predictions["model"].unique()
    horizons = sorted(
        predictions["horizon"].unique()
    )

    for horizon in horizons:
        fig, ax = plt.subplots(figsize=(10, 5))

        horizon_data = predictions[
            predictions["horizon"] == horizon
        ]

        for model in models:
            model_data = horizon_data[
                horizon_data["model"] == model
            ]

            ax.hist(
                model_data["error"],
                bins=20,
                alpha=0.45,
                label=model,
            )

        ax.axvline(
            0,
            linestyle="--",
            linewidth=1,
        )

        ax.set_xlabel(
            "Residual (actual - prediction)"
        )
        ax.set_ylabel("Frequency")
        ax.set_title(
            f"GenTD26 Residual Distribution "
            f"({horizon}h Horizon)"
        )
        ax.legend()
        ax.grid(
            axis="y",
            alpha=0.3,
        )

        fig.tight_layout()

        save_figure(
            fig,
            f"residual_distribution_{horizon}h.png",
        )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    metrics, predictions = load_data()

    plot_mae_by_horizon(metrics)

    plot_metric_comparison(metrics)

    plot_actual_vs_predicted(predictions)

    plot_error_by_hour(predictions)

    plot_zero_vs_nonzero_error(predictions)

    plot_residual_distribution(predictions)

    print("\nAll diagnostic figures generated.")


if __name__ == "__main__":
    main()
