# Daily Kyros Research Handoff

Owner: Aditi
Date: 2026-09-10
Git branch / commit: main / 174f37a

What I completed:
- Ran limited external validation using the official Numenta Anomaly Benchmark series `realKnownCause/ec2_request_latency_system_failure.csv` and the source's official anomaly windows.
- Fitted a univariate Isolation Forest only on normal observations in the chronological training split.
- Selected the alert threshold on validation only and evaluated eligible, non-straddling test windows.

Exact command to reproduce:
`python -m experiments.anomaly.run_dataset_b_evaluation --source data\external\NAB\data\realKnownCause\ec2_request_latency_system_failure.csv --windows data\external\NAB\labels\combined_windows.json --series-key realKnownCause/ec2_request_latency_system_failure.csv --run-id dataset_b_nab_001`

Input dataset + hash/version:
- NAB repository commit: `ea702d75cc2258d9d7dd35ca8e5e2539d71f3140`
- Source SHA-256: `1a0112add1e69052d2b2075624fc8c3ec436a9fc94ae6be31347db0aac8f9dd7`
- Label-window SHA-256: `164294d56679e33a9323f6b3824754183dbf661e31848f328bfc57019df804c4`

Run ID(s): `dataset_b_nab_001`

Result files:
- `results/dataset_b_nab_001/metrics.json`
- `results/dataset_b_nab_001/event_alert_table.csv`
- `results/dataset_b_nab_001/false_alert_table.csv`
- `results/dataset_b_nab_001/hourly_or_source_interval_scores.csv`
- `results/dataset_b_nab_001/adapter_report.json`
- `results/dataset_b_nab_001/run_metadata.json`

Key metric(s):
- Event recall: 0.500 across 2 eligible test events.
- PR-AUC: 0.323; ROC-AUC: 0.493.
- False-alert intervals: 0; false-alert rate: 0.000 per 100 normal source rows.

What failed / limitation:
This is univariate NAB anomaly-window validation. NAB's `value` is retained as `source_metric_value`; it is not API latency, traffic, error rate, CPU, or database latency. Warning lead time is invalid because NAB does not label a separate pre-onset warning window.

What I need from another teammate:
Amulya must confirm that RCA output maps to the frozen causes: `none`, `traffic_surge`, `service_delay`, `database_slowdown`, and `application_error_burst`.

Can another teammate reproduce this? Yes, after cloning the official NAB repository into `data/external/NAB` with the documented series and labels available.
