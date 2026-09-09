# Anomaly and Early Warning Protocol

## Frozen question

Can multivariate anomaly detection identify labelled degradation earlier than reactive thresholds?

## Scope and ownership

Aditi owns the controlled data and scenario harness, anomaly detection, early-warning evaluation, Dataset B anomaly validation, and handoff artifacts. The existing candidate is Isolation Forest on hourly operational signals. The required simple baseline is a robust univariate response-latency detector fitted with train-normal median and MAD.

## Data and splits

Dataset A is controlled synthetic API telemetry with known generated ground truth. It is generated from a frozen JSON configuration. Dataset B is external validation only and its valid metrics depend on its documented source semantics. Isolation Forest, scaling, and the robust baseline are fitted only on normal training episodes. Validation selects detector score thresholds. Test episodes are never used to select a detector, feature set, contamination setting, threshold, or reactive threshold.

Telemetry is split chronologically into train, validation, and test episodes. Random row-level splitting is prohibited. The model input signals are `request_count`, `response_time_ms`, `error_rate`, `cpu_usage`, and `db_latency_ms`.

## Labels and event convention

The warning window is `[warning_start_time_utc, event_onset_time_utc)`. The event window is `[event_onset_time_utc, event_end_time_utc]`. Event recall counts an alert from warning-window start through event end. Early-warning recall counts an alert before onset. Lead time is event onset minus the first valid warning-window alert and is reported only for early-warned events. A false alert is an alert outside every frozen warning and event window.

## Detectors

The robust baseline uses response latency median and MAD fitted on normal training rows. Isolation Forest uses request count, response latency, error rate, CPU usage, and DB latency after RobustScaler fitting on normal training rows. Both retain continuous anomaly scores. Thresholds are selected on validation under the configured false-alert budget.

## Metrics

Primary metrics are event recall, PR-AUC where continuous scores and labels are valid, false-alert rate, and median warning lead time. Secondary metrics are event precision, event F1, ROC-AUC, and lead-time IQR. Adjacent hourly alert rows are merged into one alert interval before false alerts are counted.

## Reactive baseline

Reactive monitoring alerts when latency is at least 500 ms or error rate is at least 5 percent. These values are frozen in `configs/anomaly_protocol.json` and must not be changed after test evaluation starts.

## Dataset B boundary

The selected limited Dataset B is the Numenta Anomaly Benchmark. It can support an external labelled anomaly sensitivity result, but does not supply the full API telemetry feature set or an independently labelled pre-onset warning period. It must not be used to claim multivariate API validation or Dataset B warning lead time. See `docs/data_dictionary/dataset_b_decision.md`.

## Reproducibility

```powershell
python -m pytest tests/test_scenarios.py tests/test_splits.py tests/test_anomaly_evaluation.py
python -m experiments.scenarios.generator --config configs/anomaly_protocol.json
python -m experiments.anomaly.run_experiment --config configs/anomaly_protocol.json --run-id anomaly_final_001
```
