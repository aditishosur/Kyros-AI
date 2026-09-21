
"""Integration tests for the frozen Dataset A RCA evaluation."""

from pathlib import Path

import pandas as pd

from experiments.rca.run_dataset_a import (
    TRUTH_LABELS,
    evaluate_dataset,
    build_confusion,
    build_class_metrics,
)


DATA_DIR = Path("data/processed/controlled_anomaly")


def test_dataset_a_episode_counts_and_splits():
    telemetry = pd.read_csv(DATA_DIR / "telemetry.csv")
    manifest = pd.read_csv(DATA_DIR / "manifest.csv")

    predictions, _, _ = evaluate_dataset(
        telemetry,
        manifest,
        prediction_hour=131,
    )

    assert len(predictions) == 100
    assert predictions["episode_id"].is_unique

    assert predictions["split"].value_counts().to_dict() == {
        "train": 10,
        "validation": 45,
        "test": 45,
    }


def test_held_out_results_and_label_mapping():
    telemetry = pd.read_csv(DATA_DIR / "telemetry.csv")
    manifest = pd.read_csv(DATA_DIR / "manifest.csv")

    predictions, _, _ = evaluate_dataset(
        telemetry,
        manifest,
        prediction_hour=131,
    )

    test = predictions[predictions["split"] == "test"]

    assert len(test) == 45
    assert set(test["true_label"]) == set(TRUTH_LABELS)

    # These are regression checks for the frozen Dataset A and RCA rules,
    # not universal performance guarantees.
    assert int(test["correct"].sum()) == 20

    assert (
        test.loc[
            test["true_label"] == "traffic_surge",
            "predicted_label",
        ]
        .eq("ELEVATED_RISK")
        .all()
    )

    assert (
        test.loc[
            test["true_label"] == "service_delay",
            "predicted_label",
        ]
        .eq("ELEVATED_RISK")
        .all()
    )

    # Fallback must not be silently interpreted as a normal diagnosis.
    assert (
        test.loc[
            test["predicted_label"] == "ELEVATED_RISK",
            "comparable_label",
        ]
        .eq("unsupported")
        .all()
    )


def test_test_only_metrics_exclude_other_splits():
    telemetry = pd.read_csv(DATA_DIR / "telemetry.csv")
    manifest = pd.read_csv(DATA_DIR / "manifest.csv")

    predictions, _, _ = evaluate_dataset(
        telemetry,
        manifest,
        prediction_hour=131,
    )

    test = predictions[predictions["split"] == "test"].copy()

    confusion = build_confusion(test)
    class_metrics = build_class_metrics(test)

    assert int(confusion.to_numpy().sum()) == 45
    assert int(class_metrics["episodes"].sum()) == 45
    assert int(class_metrics["correct"].sum()) == 20
