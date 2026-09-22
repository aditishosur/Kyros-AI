# Aditi Integration Handoff

## Frozen Inputs

The integration experiment must use the frozen Dataset A run `anomaly_final_001` and must not recompute detector thresholds. The scenario manifest is `results/anomaly_final_001/predictions/scenario_manifest.csv`. It supplies `episode_id`, `endpoint`, `scenario`, `primary_cause`, `warning_start_time_utc`, `event_onset_time_utc`, and `event_end_time_utc`.

The frozen primary-cause vocabulary is `none`, `traffic_surge`, `service_delay`, `database_slowdown`, and `application_error_burst`. The integration table must preserve these labels without silently remapping them. Current RCA outputs are not one-to-one with this vocabulary, so unavailable or unsupported RCA mappings must be reported as unavailable rather than counted as correct.

## Alert and Timing Inputs

Use `results/anomaly_final_001/metrics/event_alert_table.csv` for detector-level first-alert timing. Its required fields are `detector`, `episode_id`, `event_onset_time`, `first_alert_time`, `detected_by_event_end`, `early_warning`, and `lead_time_hours`.

Use `results/anomaly_final_001/predictions/hourly_alert_scores.csv` only when the integration script needs the first timestamp for a specific alert column. Relevant columns are `iforest_alert`, `baseline_alert`, and `reactive_alert`, together with `episode_id` and `timestamp`.

For the shared integration table, the Aditi-owned fields are:

| Field | Source | Meaning |
| --- | --- | --- |
| `episode_id` | Scenario manifest | Held-out controlled episode identifier |
| `primary_cause` | Scenario manifest | Frozen generated ground-truth cause |
| `event_onset_time` | Scenario manifest | Beginning of the labelled event window |
| `first_anomaly_alert` | Event alert table where `detector=isolation_forest` | First Isolation Forest alert in the valid warning or event window, if present |
| `first_robust_alert` | Event alert table where `detector=robust_latency_baseline` | First robust-baseline alert in the valid warning or event window, if present |
| `first_reactive_breach` | Event alert table where `detector=reactive_threshold` | First latency-or-error reactive alert in the valid warning or event window, if present |
| `anomaly_early_warning` | Event alert table where `detector=isolation_forest` | Whether the first valid Isolation Forest alert occurs before event onset |
| `anomaly_lead_time_hours` | Event alert table where `detector=isolation_forest` | Event onset minus first valid warning alert; blank when not early warned |

The table must keep first forecast warning, first valid RCA output, and first simulation output as separate columns supplied by their respective owners. Do not combine their timings into one composite score.

## Reproduction

Run the following before consuming the artifacts:

```powershell
python -m pytest tests/test_scenarios.py tests/test_splits.py tests/test_anomaly_evaluation.py tests/test_dataset_b.py
python -m experiments.scenarios.generator --config configs/anomaly_protocol.json
python -m experiments.anomaly.run_experiment --config configs/anomaly_protocol.json --run-id anomaly_final_001
```

The Dataset B NAB command is intentionally excluded from the integration experiment because NAB does not contain the controlled API-cause labels or a separate warning window.
