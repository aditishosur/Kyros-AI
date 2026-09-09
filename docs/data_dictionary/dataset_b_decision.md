# Dataset B Decision

Decision: use the Numenta Anomaly Benchmark only as limited external labelled anomaly validation.

NAB is a streaming anomaly benchmark with labelled anomaly windows and real-world series. It is appropriate for a limited external result: score-based anomaly discrimination, event recall from labelled anomaly windows, and false-alert behaviour. The Numenta repository states an MIT licence.

NAB is not semantically equivalent to the controlled API telemetry dataset. It does not supply the full Kyros feature set of request count, response latency, error rate, CPU usage, and database latency. Therefore, the multivariate Isolation Forest result remains Dataset A only. Do not claim that NAB validates multivariate API degradation detection.

NAB anomaly windows can define labelled anomaly events, but do not provide the separate pre-onset warning period required by the frozen lead-time convention. Do not report Dataset B warning lead time. Report this limitation prominently in the paper.

Valid Dataset B metrics: score-based PR-AUC, ROC-AUC, anomaly-window event recall, and false-alert behaviour, provided the adapter retains the source label windows.

Invalid Dataset B metrics: multivariate Isolation Forest comparison, API-latency threshold comparison, API-error threshold comparison, root-cause accuracy, and warning lead time. These are invalid because NAB does not supply the required API signal meanings or a distinct labelled pre-onset warning period.

Meaning lost in mapping: NAB's generic source `value` remains `source_metric_value`; it is not treated as API latency, request volume, error rate, CPU usage, or DB latency.

Official source: <https://github.com/numenta/NAB>

Licence: <https://github.com/numenta/NAB/blob/master/LICENSE.txt>
