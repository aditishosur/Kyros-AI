from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class TemporalSplit:
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame


def chronological_split(
    df: pd.DataFrame,
    train_fraction: float = 0.60,
    validation_fraction: float = 0.20,
) -> TemporalSplit:
    """
    Split the dataset chronologically by unique timestamp.

    Default split:
        60% train
        20% validation
        20% test

    The split is performed at the timestamp level so that all endpoints
    belonging to the same timestamp remain in the same split.
    """

    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1")

    if not 0 < validation_fraction < 1:
        raise ValueError("validation_fraction must be between 0 and 1")

    if train_fraction + validation_fraction >= 1:
        raise ValueError(
            "train_fraction + validation_fraction must be < 1"
        )

    data = df.copy()

    # Normalize timestamps to UTC.
    data["timestamp"] = pd.to_datetime(
        data["timestamp"],
        utc=True,
    )

    # Ensure deterministic ordering.
    data = (
        data.sort_values(["timestamp", "endpoint"])
        .reset_index(drop=True)
    )

    # Split using unique timestamps.
    timestamps = (
        data["timestamp"]
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )

    n_timestamps = len(timestamps)

    if n_timestamps < 3:
        raise ValueError(
            "Dataset must contain at least 3 unique timestamps."
        )

    # round() gives the intended 60/20/20 split for 336 timestamps:
    # 202 train + 67 validation + 67 test.
    train_end = round(
        n_timestamps * train_fraction
    )

    validation_end = (
        train_end
        + round(n_timestamps * validation_fraction)
    )

    train_timestamps = set(
        timestamps.iloc[:train_end]
    )

    validation_timestamps = set(
        timestamps.iloc[train_end:validation_end]
    )

    test_timestamps = set(
        timestamps.iloc[validation_end:]
    )

    train = data[
        data["timestamp"].isin(train_timestamps)
    ].copy()

    validation = data[
        data["timestamp"].isin(validation_timestamps)
    ].copy()

    test = data[
        data["timestamp"].isin(test_timestamps)
    ].copy()

    return TemporalSplit(
        train=train.reset_index(drop=True),
        validation=validation.reset_index(drop=True),
        test=test.reset_index(drop=True),
    )


def verify_split(split: TemporalSplit) -> None:
    """
    Verify that the temporal split has:

    - no timestamp overlap
    - strict chronological ordering
    - non-empty train/validation/test sets
    """

    train_ts = set(split.train["timestamp"])
    validation_ts = set(split.validation["timestamp"])
    test_ts = set(split.test["timestamp"])

    # No overlap.
    if train_ts & validation_ts:
        raise AssertionError(
            "Train/validation timestamp overlap detected."
        )

    if validation_ts & test_ts:
        raise AssertionError(
            "Validation/test timestamp overlap detected."
        )

    if train_ts & test_ts:
        raise AssertionError(
            "Train/test timestamp overlap detected."
        )

    # Strict chronology.
    if not (
        split.train["timestamp"].max()
        < split.validation["timestamp"].min()
    ):
        raise AssertionError(
            "Train is not strictly before validation."
        )

    if not (
        split.validation["timestamp"].max()
        < split.test["timestamp"].min()
    ):
        raise AssertionError(
            "Validation is not strictly before test."
        )

    # Non-empty.
    if split.train.empty:
        raise AssertionError("Train split is empty.")

    if split.validation.empty:
        raise AssertionError("Validation split is empty.")

    if split.test.empty:
        raise AssertionError("Test split is empty.")

    print("Temporal split verification: PASS")
    print(
        f"Train:      "
        f"{split.train['timestamp'].nunique()} timestamps, "
        f"{len(split.train)} rows"
    )
    print(
        f"Validation: "
        f"{split.validation['timestamp'].nunique()} timestamps, "
        f"{len(split.validation)} rows"
    )
    print(
        f"Test:       "
        f"{split.test['timestamp'].nunique()} timestamps, "
        f"{len(split.test)} rows"
    )