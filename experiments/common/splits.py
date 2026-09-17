from __future__ import annotations

import pandas as pd


VALID_SPLITS = {"train", "validation", "test"}


def validate_episode_splits(manifest: pd.DataFrame) -> None:
    """Ensure every generated episode belongs to exactly one declared split."""
    required = {"episode_id", "split", "start_time_utc", "event_end_time_utc"}
    missing = required.difference(manifest.columns)
    if missing:
        raise ValueError(f"Manifest is missing required columns: {sorted(missing)}")
    if not set(manifest["split"]).issubset(VALID_SPLITS):
        raise ValueError("Manifest contains an unknown split")
    if manifest["episode_id"].duplicated().any():
        raise ValueError("Each manifest episode_id must be unique")


def validate_telemetry_episode_splits(frame: pd.DataFrame) -> None:
    """Reject telemetry where a single episode is split across temporal partitions."""
    required = {"episode_id", "split"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Telemetry is missing required columns: {sorted(missing)}")
    per_episode = frame.groupby("episode_id")["split"].nunique()
    crossing = per_episode[per_episode > 1]
    if not crossing.empty:
        raise ValueError(f"Episodes may not straddle splits: {sorted(crossing.index.tolist())}")


def normal_training_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Return the only rows permitted to fit anomaly models."""
    mask = (frame["split"] == "train") & (frame["scenario"] == "normal")
    normal = frame.loc[mask].copy()
    if normal.empty:
        raise ValueError("No normal training rows are available for detector fitting")
    return normal
