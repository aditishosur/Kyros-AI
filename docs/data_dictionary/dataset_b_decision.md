# Dataset B Decision

Decision: use the Numenta Anomaly Benchmark only as limited external labelled anomaly validation. The reproducible implementation evaluates a single official NAB series with its official anomaly windows, using a univariate Isolation Forest fitted on chronological normal-training observations only.

NAB is a streaming anomaly benchmark with labelled anomaly windows and real-world series. It is appropriate for a limited external result: score-based anomaly discrimination, event recall from labelled anomaly windows, and false-alert behaviour. The Numenta repository states an MIT licence.

NAB is not semantically equivalent to the controlled API telemetry dataset. It does not supply the full Kyros feature set of request count, response latency, error rate, CPU usage, and database latency. Therefore, the multivariate Isolation Forest result remains Dataset A only. Do not claim that NAB validates multivariate API degradation detection.

NAB anomaly windows can define labelled anomaly events, but do not provide the separate pre-onset warning period required by the frozen lead-time convention. Do not report Dataset B warning lead time. Report this limitation prominently in the paper.

Valid Dataset B metrics: score-based PR-AUC, ROC-AUC, anomaly-window event recall, and false-alert behaviour, provided the adapter retains the source label windows.

Invalid Dataset B metrics: multivariate Isolation Forest comparison, API-latency threshold comparison, API-error threshold comparison, root-cause accuracy, and warning lead time. These are invalid because NAB does not supply the required API signal meanings or a distinct labelled pre-onset warning period.

Meaning lost in mapping: NAB's generic source `value` remains `source_metric_value`; it is not treated as API latency, request volume, error rate, CPU usage, or DB latency.

Official source: <https://github.com/numenta/NAB>

Licence: <https://github.com/numenta/NAB/blob/master/LICENSE.txt>

## Reproduction

Clone the official NAB repository into `data/external/NAB/`; the raw source files are intentionally Git-ignored. Then run:

```powershell
python -m experiments.anomaly.run_dataset_b_evaluation `
  --source data/external/NAB/data/realKnownCause/ec2_request_latency_system_failure.csv `
  --windows data/external/NAB/labels/combined_windows.json `
  --series-key realKnownCause/ec2_request_latency_system_failure.csv `
  --run-id dataset_b_nab_001
```

The result must be described as **univariate labelled NAB anomaly-window validation**. It is not a five-feature API telemetry result and it has no valid warning-lead-time metric.
