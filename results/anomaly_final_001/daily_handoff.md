DAILY KYROS RESEARCH HANDOFF

Owner: Aditi
Date: 2026-09-09
Git branch / commit: main / e8e82ad522a542de7731a71f8efbd8c20290e8b5

What I completed:
- Froze the controlled scenario taxonomy and cause labels.
- Created Dataset A controlled synthetic API telemetry.
- Generated 16,800 hourly telemetry rows and 100 scenario-manifest rows.
- Implemented a robust median/MAD response-latency baseline.
- Implemented multivariate Isolation Forest using request count, latency, error rate, CPU usage, and DB latency.
- Compared both detectors with fixed reactive latency/error thresholds.
- Selected alert thresholds using validation data only.
- Evaluated the locked configuration on held-out test episodes.
- Saved scores, alerts, metrics, false-alert intervals, an alert timeline, and reproducibility metadata.

Exact command to reproduce:
python -m experiments.anomaly.run_experiment --config configs\anomaly_protocol.json --run-id anomaly_final_001

Input dataset + hash/version:
Controlled synthetic Dataset A, controlled_dataset_v1
Telemetry SHA-256: FD7FC291BC9640F2B2475274688CBDD5CBE888C5716265D58874FF492DF73A7A

Run ID(s):
anomaly_final_001

Result files:
- results/anomaly_final_001/metrics/anomaly_metrics.csv
- results/anomaly_final_001/metrics/event_alert_table.csv
- results/anomaly_final_001/metrics/false_alert_table.csv
- results/anomaly_final_001/predictions/hourly_alert_scores.csv
- results/anomaly_final_001/predictions/scenario_manifest.csv
- results/anomaly_final_001/figures/alert_timeline.html
- results/anomaly_final_001/locked_detector_config.json
- results/anomaly_final_001/run_metadata.json

Key metric(s):
Robust baseline: event recall 0.800, early-warning recall 0.200, PR-AUC 0.604, false-alert rate 0.915 per 100 normal hours, median lead time 9.5 hours.
Isolation Forest: event recall 1.000, early-warning recall 0.125, PR-AUC 0.680, false-alert rate 1.144 per 100 normal hours, median lead time 11.0 hours.
Reactive threshold: event recall 0.725, early-warning recall 0.000, false-alert rate 0.000 per 100 normal hours.

What failed / limitation:
Dataset B is NAB, used only as limited external labelled anomaly validation. It cannot validate multivariate API anomaly detection, API latency/error thresholds, RCA, or the warning lead-time metric.

What I need from another teammate:
Amulya must confirm that RCA output maps to these frozen causes: none, traffic_surge, service_delay, database_slowdown, application_error_burst.

Can another teammate reproduce this?
Yes, after installing requirements.txt and running the exact command above.
