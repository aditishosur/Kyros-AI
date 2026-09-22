# Datasets and Anomaly Methodology

## Controlled Dataset A

Dataset A is controlled synthetic hourly API telemetry generated from a frozen scenario protocol. Each episode contains five operational signals: request count, response latency in milliseconds, error rate, CPU usage, and database latency in milliseconds. The frozen essential scenarios are normal operation, traffic spike, latency increase, database slowdown, and 5xx error burst. Every episode has an endpoint, seed, scenario, intensity, severity, primary cause, warning-window start, event onset, and event end in the manifest.

Episodes are assigned to chronological train, validation, or held-out test partitions. The configuration uses ten normal-training seeds, five normal-validation seeds, five normal-test seeds, ten validation-event seeds, and ten test-event seeds. Validation intensities are 0.4 and 0.8; held-out test intensities are 1.2 and 1.6. No episode straddles a split. The frozen cause vocabulary is `none`, `traffic_surge`, `service_delay`, `database_slowdown`, and `application_error_burst`.

The warning window is the half-open interval from `warning_start_time_utc` through, but excluding, event onset. The event window starts at event onset and ends at `event_end_time_utc`, inclusive. An event is detected when an alert occurs anywhere from warning-window start through event end. An early warning is an alert before event onset. Lead time is event onset minus the first early-warning alert; it is calculated only for early-warned events. Adjacent hourly alerts are merged into alert intervals before false alerts are counted. A false alert is an alert outside every frozen warning and event window.

## Detectors and Selection

The required baseline is a robust univariate latency detector. It fits the response-latency median and median absolute deviation (MAD) on normal training observations only and retains a continuous robust score. The multivariate candidate is Isolation Forest with RobustScaler preprocessing, using request count, response latency, error rate, CPU usage, and database latency. Its scaler and model are fitted on normal training observations only. The contamination setting is fixed at 0.02; it is not derived from test anomaly prevalence.

For both detector families, alert-score thresholds are selected on validation data under a frozen false-alert budget of one alert interval per 100 normal hours. The resulting locked thresholds are 1.689265145355797 for the robust baseline and 0.5736460787259643 for Isolation Forest. Held-out test episodes are not used to choose features, contamination, thresholds, or reactive thresholds.

The reactive comparator raises an alert when response latency is at least 500 ms or error rate is at least 5 percent. This comparator is intentionally reactive and has no learned parameters.

Primary metrics are event recall, PR-AUC, false-alert rate, and median warning lead time. Secondary metrics are event precision, event F1, ROC-AUC, and lead-time IQR. Continuous scores, timestamped alerts, event-level alert tables, false-alert tables, detector metadata, and a representative alert timeline are retained as reproducibility artifacts.

## External Dataset B

Dataset B is the Numenta Anomaly Benchmark (NAB), used only for limited external labelled anomaly-window validation. A single official NAB series is retained with its generic `value` column renamed to `source_metric_value`; it is not interpreted as API latency, request count, error rate, CPU usage, or database latency. A univariate Isolation Forest is fitted only on normal observations in a chronological training segment, its threshold is selected on validation, and only official anomaly windows wholly contained in the test split are eligible for event scoring.

NAB supports score-based PR-AUC, ROC-AUC, anomaly-window event recall, and false-alert behavior. It cannot validate the five-feature API detector, API reactive thresholds, RCA, or the frozen warning-lead-time convention because it does not provide a separate labelled pre-onset warning interval. Results from Dataset A and Dataset B are therefore reported as distinct evidence layers.
