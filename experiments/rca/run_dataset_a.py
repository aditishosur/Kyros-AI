
"""Evaluate frozen Kyros RCA rules on Dataset A, one prediction per episode."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from backend.services.rca_rules import determine_root_cause
from experiments.common.cause_taxonomy import normalize_kyros_cause
from experiments.rca.input_adapter import derive_rca_signals


TRUTH_LABELS = (
    "none",
    "traffic_surge",
    "service_delay",
    "database_slowdown",
    "application_error_burst",
)

# Only these two Kyros outputs have an unambiguous match to Dataset A's
# frozen primary-cause labels. Do not treat fallback as "none".
PREDICTION_TO_TRUTH = {
    "DB_LATENCY": "database_slowdown",
    "APPLICATION_ERROR": "application_error_burst",
}


def build_confusion(predictions: pd.DataFrame) -> pd.DataFrame:
    """Build a cross-taxonomy confusion matrix."""

    confusion = pd.crosstab(
        pd.Categorical(
            predictions["true_label"],
            categories=TRUTH_LABELS,
        ),
        predictions["predicted_label"],
        dropna=False,
    )

    confusion.index.name = "true_label"
    return confusion


def build_class_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    """Calculate exact-match recall for each ground-truth cause."""

    rows = []

    for label in TRUTH_LABELS:
        subset = predictions[predictions["true_label"] == label]

        rows.append(
            {
                "true_label": label,
                "episodes": len(subset),
                "correct": int(subset["correct"].sum()),
                "recall": (
                    float(subset["correct"].mean())
                    if len(subset)
                    else float("nan")
                ),
            }
        )

    return pd.DataFrame(rows)


def evaluate_dataset(
    telemetry: pd.DataFrame,
    manifest: pd.DataFrame,
    prediction_hour: int = 131,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return episode predictions, cross-taxonomy confusion, and class metrics."""

    if prediction_hour < 7:
        raise ValueError(
            "prediction_hour must allow an earlier traffic baseline"
        )

    required_manifest = {
        "episode_id",
        "split",
        "primary_cause",
    }

    missing = required_manifest - set(manifest.columns)

    if missing:
        raise ValueError(
            f"Missing manifest columns: {sorted(missing)}"
        )

    if manifest["episode_id"].duplicated().any():
        raise ValueError("Manifest contains duplicate episode IDs")

    if not manifest["primary_cause"].isin(TRUTH_LABELS).all():
        raise ValueError(
            "Manifest contains unknown ground-truth causes"
        )

    groups = {
        episode_id: group.sort_values("timestamp")
        for episode_id, group in telemetry.groupby(
            "episode_id",
            sort=False,
        )
    }

    rows = []

    for record in manifest.itertuples(index=False):
        episode_id = record.episode_id

        if episode_id not in groups:
            raise ValueError(
                f"Missing telemetry for episode {episode_id}"
            )

        episode = groups[episode_id]

        if len(episode) <= prediction_hour:
            raise ValueError(
                f"Insufficient telemetry for {episode_id}"
            )

        if (
            "split" in episode.columns
            and not episode["split"].eq(record.split).all()
        ):
            raise ValueError(
                f"Split mismatch for {episode_id}"
            )

        prediction_time = episode.iloc[prediction_hour]["timestamp"]

        signals = derive_rca_signals(
            episode,
            prediction_time,
        )

        cause, _ = determine_root_cause(
            traffic=signals.traffic,
            db_latency=signals.db_latency,
            errors=signals.errors,
        )

        predicted_label = normalize_kyros_cause(cause)

        comparable_label = PREDICTION_TO_TRUTH.get(
            predicted_label
        )

        correct = comparable_label == record.primary_cause

        rows.append(
            {
                "episode_id": episode_id,
                "split": record.split,
                "true_label": record.primary_cause,
                "predicted_label": predicted_label,
                "comparable_label": (
                    comparable_label or "unsupported"
                ),
                "correct": bool(correct),
                "prediction_time": prediction_time,
                "traffic_delta_pct": signals.traffic,
                "db_latency_delta_pct": signals.db_latency,
                "error_rate_pct": signals.errors,
                "response_latency_delta_pct": (
                    signals.response_latency
                ),
            }
        )

    predictions = pd.DataFrame(rows)

    confusion = build_confusion(predictions)
    class_metrics = build_class_metrics(predictions)

    return predictions, confusion, class_metrics


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate frozen Kyros RCA rules on Dataset A."
    )

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/processed/controlled_anomaly"),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/rca_dataset_a_v1"),
    )

    parser.add_argument(
        "--prediction-hour",
        type=int,
        default=131,
    )

    args = parser.parse_args()

    # Load the frozen Dataset A telemetry and episode manifest.
    telemetry = pd.read_csv(
        args.data_dir / "telemetry.csv"
    )

    manifest = pd.read_csv(
        args.data_dir / "manifest.csv"
    )

    predictions, confusion, class_metrics = evaluate_dataset(
        telemetry,
        manifest,
        args.prediction_hour,
    )

    args.output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Save results across all dataset splits.
    predictions.to_csv(
        args.output_dir / "episode_predictions.csv",
        index=False,
    )

    confusion.to_csv(
        args.output_dir / "cross_taxonomy_confusion.csv"
    )

    class_metrics.to_csv(
        args.output_dir / "per_class_metrics.csv",
        index=False,
    )

    print("RCA Dataset A evaluation")
    print(f"Prediction hour: {args.prediction_hour}")
    print(f"Total episodes: {len(predictions)}")

    for split, subset in predictions.groupby("split"):
        accuracy = float(subset["correct"].mean())

        unsupported_count = int(
            subset["comparable_label"]
            .eq("unsupported")
            .sum()
        )

        print(
            f"{split}: {len(subset)} episodes; "
            f"exact-match accuracy={accuracy:.4f}; "
            f"unsupported predictions={unsupported_count}"
        )

    # Save and display HELD-OUT TEST results separately.
    # Everything below remains inside main().
    test = predictions[
        predictions["split"] == "test"
    ].copy()

    if not test.empty:
        test.to_csv(
            args.output_dir / "test_episode_predictions.csv",
            index=False,
        )

        test_confusion = build_confusion(test)

        test_confusion.to_csv(
            args.output_dir / "test_cross_taxonomy_confusion.csv"
        )

        test_class_metrics = build_class_metrics(test)

        test_class_metrics.to_csv(
            args.output_dir / "test_per_class_metrics.csv",
            index=False,
        )

        test_accuracy = float(
            test["correct"].mean()
        )

        test_correct = int(
            test["correct"].sum()
        )

        print("\nHeld-out test results:")
        print(
            f"Correct diagnoses: "
            f"{test_correct}/{len(test)}"
        )
        print(
            f"Exact-match accuracy: "
            f"{test_accuracy:.4f}"
        )

        print("\nHeld-out test confusion matrix:")
        print(test_confusion)

        print("\nHeld-out test per-class metrics:")
        print(test_class_metrics.to_string(index=False))

        normal_controls = test[
            test["true_label"] == "none"
        ]

        if not normal_controls.empty:
            fallback_rate = float(
                normal_controls["predicted_label"]
                .eq("ELEVATED_RISK")
                .mean()
            )

            print(
                "\nNormal-control fallback rate: "
                f"{fallback_rate:.4f}"
            )

            print(
                "Note: ELEVATED_RISK is a nonspecific "
                "fallback, not an explicit normal prediction."
            )

    print(
        f"\nSaved results to {args.output_dir}"
    )


if __name__ == "__main__":
    main()
