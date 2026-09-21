from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score


def alert_intervals(frame: pd.DataFrame, alert_column: str) -> pd.DataFrame:
    """Merge adjacent alerts into one interval so alerts are not double counted."""
    alerted = frame.loc[frame[alert_column]].sort_values(["endpoint", "timestamp"]).copy()
    if alerted.empty:
        return pd.DataFrame(columns=["endpoint", "alert_start", "alert_end", "duration_hours"])
    alerted["new_interval"] = (
        alerted.groupby("endpoint")["timestamp"].diff().dt.total_seconds().div(3600).fillna(2).ne(1)
    )
    alerted["interval_id"] = alerted.groupby("endpoint")["new_interval"].cumsum()
    return (
        alerted.groupby(["endpoint", "interval_id"], as_index=False)
        .agg(alert_start=("timestamp", "min"), alert_end=("timestamp", "max"), duration_hours=("timestamp", "size"))
        .drop(columns="interval_id")
    )


def select_threshold(scores: np.ndarray, validation: pd.DataFrame, score_column: str, budget_per_100_hours: float) -> float:
    """Choose a validation-only threshold under a fixed false-alert budget."""
    candidates = np.unique(np.quantile(scores, np.linspace(0.85, 0.999, 80)))
    records = []
    for threshold in candidates:
        probe = validation.copy()
        probe["candidate_alert"] = probe[score_column] >= threshold
        normal_hours = int((~probe["evaluation_positive"]).sum())
        false_intervals = len(alert_intervals(probe.loc[~probe["evaluation_positive"]], "candidate_alert"))
        false_rate = false_intervals / max(normal_hours, 1) * 100
        event_rows = probe.loc[probe["is_event"]]
        event_recall_proxy = float(event_rows["candidate_alert"].mean()) if not event_rows.empty else 0.0
        records.append((threshold, false_rate, event_recall_proxy))
    allowed = [row for row in records if row[1] <= budget_per_100_hours]
    # Favour event sensitivity under the declared false-alert constraint, then a stricter threshold.
    winner = max(allowed or records, key=lambda row: (row[2], -row[1], row[0]))
    return float(winner[0])


def event_alert_table(frame: pd.DataFrame, manifest: pd.DataFrame, alert_column: str) -> pd.DataFrame:
    rows = []
    events = manifest.loc[manifest["scenario"] != "normal"].copy()
    for event in events.itertuples(index=False):
        episode = frame.loc[frame["episode_id"] == event.episode_id].sort_values("timestamp")
        warnings = episode.loc[episode["is_warning"] & episode[alert_column]]
        detectable = episode.loc[(episode["is_warning"] | episode["is_event"]) & episode[alert_column]]
        first_warning = warnings["timestamp"].min() if not warnings.empty else pd.NaT
        first_detectable = detectable["timestamp"].min() if not detectable.empty else pd.NaT
        onset = pd.Timestamp(event.event_onset_time_utc)
        rows.append({
            "episode_id": event.episode_id,
            "split": event.split,
            "scenario": event.scenario,
            "primary_cause": event.primary_cause,
            "endpoint": event.endpoint,
            "event_onset_time": onset,
            "event_end_time": pd.Timestamp(event.event_end_time_utc),
            "first_alert_time": first_detectable,
            "detected_by_event_end": not pd.isna(first_detectable),
            "early_warning": not pd.isna(first_warning),
            "lead_time_hours": (onset - first_warning).total_seconds() / 3600 if not pd.isna(first_warning) else np.nan,
        })
    return pd.DataFrame(rows)


def detector_metrics(frame: pd.DataFrame, manifest: pd.DataFrame, detector: str, score_column: str, alert_column: str) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    evaluated = frame.loc[frame["split"] == "test"].copy()
    table = event_alert_table(evaluated, manifest.loc[manifest["split"] == "test"], alert_column)
    false_rows = evaluated.loc[~evaluated["evaluation_positive"]].copy()
    false_rows["is_false_alert"] = false_rows[alert_column]
    false_table = alert_intervals(false_rows, "is_false_alert")
    false_table.insert(0, "detector", detector)
    false_table["reason"] = "Alert outside all frozen warning and event windows"
    y_true = evaluated["evaluation_positive"].astype(int)
    scores = evaluated[score_column]
    pr_auc = float(average_precision_score(y_true, scores)) if y_true.nunique() == 2 else np.nan
    roc_auc = float(roc_auc_score(y_true, scores)) if y_true.nunique() == 2 else np.nan
    detected = int(table["detected_by_event_end"].sum())
    early = int(table["early_warning"].sum())
    false_count = len(false_table)
    precision = detected / max(detected + false_count, 1)
    recall = detected / max(len(table), 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-9)
    early_leads = table.loc[table["early_warning"], "lead_time_hours"].dropna()
    metrics = {
        "detector": detector,
        "event_recall": recall,
        "early_warning_recall": early / max(len(table), 1),
        "event_precision": precision,
        "event_f1": f1,
        "pr_auc": pr_auc,
        "roc_auc": roc_auc,
        "false_alerts": false_count,
        "false_alert_rate_per_100_normal_hours": false_count / max(len(false_rows), 1) * 100,
        "median_lead_time_hours": float(early_leads.median()) if not early_leads.empty else np.nan,
        "lead_time_iqr_hours": float(early_leads.quantile(0.75) - early_leads.quantile(0.25)) if len(early_leads) > 1 else np.nan,
        "events_with_early_lead_time": int(len(early_leads)),
    }
    return metrics, table, false_table
