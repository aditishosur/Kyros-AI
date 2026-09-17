# Forecasting Handoff

## 1. Purpose and Research Objective

This document provides a consolidated handoff for the forecasting experiments conducted for the Kyros-AI / PulseOps research project.

It summarizes:

- The research objective
- Dataset A and Dataset B
- Authoritative experiment runs
- Final evaluation metrics
- Feature ablation results
- Diagnostic figures and artifacts
- Reproducibility instructions
- Testing status
- Limitations
- Claims that can and cannot be made in the research paper

The primary research question is:

> Can workload forecasts beat simple temporal baselines?

The forecasting work evaluates whether a Random Forest regression model can improve workload prediction accuracy compared with simple temporal baselines.

Two datasets were evaluated:

1. **Dataset A:** Controlled synthetic API telemetry.
2. **Dataset B:** GenTD26 real-world GenAI serving trace used for external validation.

Dataset A and Dataset B are reported separately because they differ in data source, temporal structure, target construction, and experimental configuration.

---

## 2. Overall Status

| Workstream | Status |
| ---------- | ------ |
| Dataset A preprocessing | Complete |
| Dataset A temporal forecasting | Complete |
| Dataset A baseline comparison | Complete |
| Dataset A error analysis | Complete |
| Dataset A fixed-hyperparameter ablation | Complete |
| Dataset B acquisition and preprocessing | Complete |
| Dataset B temporal forecasting | Complete |
| Dataset B baseline comparison | Complete |
| Dataset B error analysis | Complete |
| Dataset B feature ablation | Complete |
| Diagnostic figures | Complete |
| Forecasting regression tests | Complete |
| Forecasting documentation | Complete |
| Paper-ready forecasting evidence | Available |

Dataset A and Dataset B results must be interpreted separately.

---

## 3. Research Protocol

### 3.1 Forecasting Horizons

Both forecasting experiments evaluate workload prediction at the following horizons where supported by the dataset-specific protocol:

- 1 hour ahead
- 6 hours ahead
- 12 hours ahead

### 3.2 Evaluation Metrics

The primary evaluation metric is:

- Mean Absolute Error (MAE)

Secondary metrics include:

- Root Mean Squared Error (RMSE)
- Symmetric Mean Absolute Percentage Error (sMAPE)
- R², where applicable

MAE is the primary comparison metric because it provides an interpretable measure of average absolute prediction error.

### 3.3 Temporal Evaluation

The experiments use chronological data splits.

The following practices are required:

- No random train/test shuffling.
- No use of future observations when constructing historical features.
- No test-set tuning.
- Validation-only model selection.
- Rolling-origin evaluation.
- Recursive forecasting for multi-step Random Forest predictions.
- Explicit separation of training, validation, and test periods.

---

## 4. Dataset A

### 4.1 Dataset Overview

Dataset A is the controlled synthetic API telemetry dataset:

```
data/api_logs.csv
```

Dataset characteristics:

| Property | Value |
| -------- | ----- |
| Total rows | 1,680 |
| API endpoints | 5 |
| Unique hourly timestamps | 336 |
| Observations per endpoint | 336 |
| Temporal resolution | Hourly |
| Target | request_count |

Endpoints:

- /payments
- /orders
- /inventory
- /identity
- /search

Relevant fields include:

- timestamp
- endpoint
- method
- status_code
- request_count
- response_time_ms
- cpu_usage
- db_latency_ms

The target variable is hourly `request_count`.

Dataset A is a controlled synthetic dataset. Its workload patterns and injected events should not be treated as equivalent to independently observed production behavior.

### 4.2 Dataset A Temporal Split

The frozen chronological split is:

| Split | Timestamps | Rows |
| ----- | ---------- | ---- |
| Train | 202 | 1,010 |
| Validation | 67 | 335 |
| Test | 67 | 335 |

Temporal ranges:

**Train**
```
2026-07-21 06:00:00 UTC to 2026-07-29 15:00:00 UTC
```

**Validation**
```
2026-07-29 16:00:00 UTC to 2026-08-01 10:00:00 UTC
```

**Test**
```
2026-08-01 11:00:00 UTC to 2026-08-04 05:00:00 UTC
```

The split is chronological and non-overlapping.

The test set is not used for hyperparameter selection.

### 4.3 Dataset A Feature Set

The frozen Random Forest feature set includes:

- hour
- day_of_week
- lag_1
- lag_3
- lag_6
- lag_24
- rolling_mean_6
- rolling_mean_24

Calendar features are derived from the timestamp being forecast.

Lag and rolling features use only historical observations available before the forecast timestamp.

### 4.4 Dataset A Recursive Forecasting

Multi-step Random Forest forecasts are generated recursively.

For every forecast step:

1. Determine the next timestamp after the latest available observation.
2. Construct a temporary feature row at that timestamp.
3. Calculate calendar features using the forecast timestamp.
4. Calculate lag and rolling features using past observations only.
5. Generate the prediction.
6. Append the generated prediction to the working history.
7. Use the generated prediction for subsequent recursive steps.

Future actual values are not used when constructing features for earlier forecast steps.

### 4.5 Dataset A Random Forest Configuration

The Random Forest configuration was selected using the validation set only.

The final configuration was:

```
n_estimators = 200
min_samples_leaf = 2
max_depth = None
random_state = 42
```

Validation mean MAE:

```
43.0845
```

The configuration was frozen before held-out test evaluation.

---

## 5. Dataset A Results

### 5.1 Aggregate Test MAE

The final Random Forest achieved the following aggregate mean MAE across all five endpoints:

| Forecast Horizon | Random Forest MAE |
| ----------------- | ------------------ |
| 1 hour | 50.807 |
| 6 hours | 66.048 |
| 12 hours | 69.729 |

Persistence baseline:

| Forecast Horizon | Persistence MAE |
| ----------------- | ---------------- |
| 1 hour | 55.255 |
| 6 hours | 118.625 |
| 12 hours | 170.916 |

Seasonal-naive baseline:

| Forecast Horizon | Seasonal Naive MAE |
| ----------------- | -------------------- |
| 1 hour | 115.098 |
| 6 hours | 118.276 |
| 12 hours | 113.320 |

### 5.2 Comparison with Persistence

The Random Forest reduced aggregate mean MAE compared with persistence by:

| Horizon | Improvement vs Persistence |
| ------- | ---------------------------- |
| 1 hour | 8.05% |
| 6 hours | 44.32% |
| 12 hours | 59.20% |

Across the 15 endpoint-horizon combinations, Random Forest achieved lower MAE than persistence in **14 / 15** cases.

The exception was:

**Endpoint:** /payments
**Horizon:** 1 hour

| Model | MAE |
| ----- | --- |
| Persistence | 52.255 |
| Random Forest | 71.416 |

Therefore, the Random Forest was better in aggregate, but persistence remained better for this specific endpoint-horizon combination.

### 5.3 Dataset A Endpoint-Level MAE

| Endpoint | 1 hour | 6 hours | 12 hours |
| -------- | ------ | ------- | -------- |
| /identity | 27.263 | 27.703 | 25.246 |
| /inventory | 37.070 | 44.787 | 40.717 |
| /orders | 51.602 | 71.350 | 74.601 |
| /payments | 71.416 | 97.572 | 122.199 |
| /search | 66.683 | 88.830 | 85.881 |

/identity had the lowest forecasting error across the evaluated endpoints.

/payments had the highest forecasting error, particularly at longer horizons.

### 5.4 Dataset A Error Analysis

The final Random Forest produced:

```
55 forecast origins × 5 endpoints × 3 horizons = 825
```

test prediction records.

Overall MAE across the prediction records:

```
62.195
```

Endpoint-level error statistics:

| Endpoint | MAE | RMSE | Mean Error |
| -------- | --- | ---- | ---------- |
| /payments | 97.062 | 132.076 | +51.282 |
| /search | 80.465 | 106.142 | +12.973 |
| /orders | 65.851 | 85.433 | +8.975 |
| /inventory | 40.858 | 53.505 | -7.139 |
| /identity | 26.737 | 33.855 | +1.535 |

Mean error is defined as:

```
actual - prediction
```

A positive mean error indicates underprediction.

The /payments endpoint showed the strongest systematic underprediction.

### 5.5 Dataset A Horizon-Level Error

| Horizon | MAE | RMSE | Mean Error |
| ------- | --- | ---- | ---------- |
| 1 hour | 50.807 | 74.649 | +3.507 |
| 6 hours | 66.048 | 93.101 | +12.856 |
| 12 hours | 69.729 | 98.846 | +24.213 |

MAE and RMSE increased with forecast horizon.

The positive mean error also increased with horizon, indicating greater aggregate underprediction at longer horizons.

### 5.6 Dataset A Largest Forecast Errors

Examples of large individual absolute errors include:

**/search**
- Timestamp: 2026-08-01 14:00 UTC
- Horizon: 1 hour
- Actual: 1119
- Prediction: 703.635
- Absolute error: 415.365
- APE: 37.12%

**/payments**
- Timestamp: 2026-08-04 04:00 UTC
- Horizon: 12 hours
- Actual: 756
- Prediction: 367.765
- Absolute error: 388.235
- APE: 51.35%

**/search**
- Timestamp: 2026-08-03 12:00 UTC
- Horizon: 12 hours
- Actual: 1012
- Prediction: 668.622
- Absolute error: 343.378
- APE: 33.93%

These cases demonstrate that large workload changes can result in substantially larger forecasting errors.

---

## 6. Dataset A Feature Ablation

### 6.1 Ablation Design

The Dataset A ablation compared:

- RF_FullFeatures
- RF_WithoutLag24

The Random Forest hyperparameters were held fixed:

```
n_estimators = 200
min_samples_leaf = 2
max_depth = None
random_state = 42
```

No additional hyperparameter selection was performed for the ablation.

Both conditions were evaluated using:

- The same held-out test period
- The same forecast horizons
- The same evaluation procedure
- The same fixed model configuration

### 6.2 Dataset A Ablation Results

| Horizon | Full Features MAE | Without lag_24 MAE | Change |
| ------- | ------------------ | -------------------- | ------ |
| 1 hour | 50.807 | 50.452 | -0.527% |
| 6 hours | 66.048 | 60.210 | -8.751% |
| 12 hours | 69.729 | 61.903 | -10.770% |

Removing lag_24 improved aggregate MAE at all three evaluated horizons.

Across the 15 endpoint-horizon combinations: **14 / 15** cases improved after removing lag_24.

The only case that became worse was /orders at the 1-hour horizon, where MAE increased by approximately 1.21%.

### 6.3 Dataset A Ablation Interpretation

Removing lag_24 did not degrade performance in this experiment and generally improved aggregate MAE.

This result is specific to:

- Dataset A
- The evaluated feature set
- The fixed Random Forest configuration
- The experimental procedure
- The evaluated temporal period

The result does not establish that 24-hour lag features are generally unnecessary for workload forecasting.

---

## 7. Dataset B

### 7.1 Dataset Overview

Dataset B uses the GenTD26 trace from the Alibaba Cluster Data repository.

Official repository:

```
https://github.com/alibaba/clusterdata/tree/master/cluster-trace-v2026-GenAI
```

The selected raw file is:

```
lora_request_trace.csv
```

Dataset B represents a real-world GenAI serving workload trace.

The timestamps are anonymized or shifted, and identifiers are hashed. Timestamps are used for chronological ordering and temporal aggregation, not as evidence of real-world wall-clock behavior.

### 7.2 Dataset B Raw Data Characteristics

| Property | Value |
| -------- | ----- |
| Total rows | 26,823 |
| Total columns | 11 |
| Time range | 2024-11-15 16:57:50 to 2024-12-08 17:33:57 |
| Approximate duration | 23 days |
| Successful requests | 26,392 |
| Failed requests | 398 |
| Pending requests | 30 |
| Processing requests | 3 |

Request types:

| Request Type | Count |
| ------------ | ----- |
| TXT_2_IMG | 24,438 |
| IMG_2_IMG | 2,199 |
| INPAINTING | 186 |

The `gmt_create` timestamp field was used to construct the hourly workload series.

The hourly aggregation follows the timestamp-based approach used in the Alibaba documentation and notebook.

### 7.3 Dataset B Target Construction

Dataset B is aggregated into a continuous hourly calendar index.

The forecasting target is:

```
request_count
```

No-event hours are represented as zero.

The resulting prepared file is:

```
data/processed/dataset_b_candidate/gentd26_hourly_request_counts.csv
```

Prepared dataset characteristics:

| Property | Value |
| -------- | ----- |
| Rows | 554 |
| Columns | 2 |
| Columns | timestamp, request_count |
| Nonzero hourly bins | 370 |
| Zero hourly bins | 184 |
| Minimum request count | 0 |
| Maximum request count | 436 |
| Missing values | None |
| Duplicate timestamps | None |

The raw Dataset B file remains outside the repository's tracked files and is ignored through .gitignore.

### 7.4 Dataset B Temporal Split

Dataset B uses a separate chronological 60/20/20 split.

| Split | Hours | Requests |
| ----- | ----- | -------- |
| Train | 332 | 13,865 |
| Validation | 111 | 7,076 |
| Test | 111 | 5,882 |

The continuous hourly index includes hours with zero requests.

The external forecasting runner validates:

- Required columns
- Unique timestamps
- Nonnegative request counts
- Continuous hourly index
- Chronological train/validation/test separation

### 7.5 Dataset B Forecasting Procedure

Dataset B uses a separate external forecasting runner:

```
experiments/forecasting/run_external_forecast.py
```

The runner:

1. Loads and validates the prepared Dataset B series.
2. Performs a chronological 60/20/20 split.
3. Selects Random Forest hyperparameters using validation data only.
4. Refits the selected configuration on the combined training and validation data.
5. Evaluates the final model on the held-out test period.
6. Uses rolling-origin forecasting.
7. Saves metadata, predictions, metrics, and validation selection artifacts.

The Dataset B Random Forest configuration was selected independently of Dataset A.

---

## 8. Dataset B Results

### 8.1 Authoritative Dataset B Run

Primary Dataset B run:

```
results/20260917T145858Z/
```

Dataset B run identifier:

```
20260917T145858Z
```

Selected Random Forest configuration:

```
n_estimators = 100
min_samples_leaf = 1
max_depth = None
```

Validation mean MAE:

```
39.5823
```

The selected configuration was chosen using validation data only.

### 8.2 Dataset B Test Metrics

**Persistence**

| Horizon | MAE | RMSE | sMAPE |
| ------- | --- | ---- | ----- |
| 1 hour | 33.212121 | 68.410821 | 86.163751 |
| 6 hours | 70.454545 | 117.655678 | 152.336284 |
| 12 hours | 102.252525 | 151.877376 | 162.876345 |

**Random Forest**

| Horizon | MAE | RMSE | sMAPE |
| ------- | --- | ---- | ----- |
| 1 hour | 22.648889 | 39.998186 | 95.227288 |
| 6 hours | 37.963636 | 64.066924 | 111.219604 |
| 12 hours | 49.380202 | 73.776128 | 112.851190 |

**Seasonal Naive**

| Horizon | MAE | RMSE | sMAPE |
| ------- | --- | ---- | ----- |
| 1 hour | 41.202020 | 79.538632 | 91.677268 |
| 6 hours | 40.383838 | 79.347338 | 93.096453 |
| 12 hours | 41.383838 | 79.710524 | Not confirmed |

The exact seasonal-naive metric values should be taken from the committed Dataset B metrics artifact when preparing final paper tables.

### 8.3 Dataset B Model Comparison

The Random Forest achieved lower aggregate MAE than persistence at all three evaluated horizons.

Compared with seasonal naive, Random Forest achieved lower MAE at the 1-hour and 6-hour horizons, but seasonal naive achieved lower MAE at the 12-hour horizon. Random Forest achieved lower RMSE than both baselines at all three horizons.

However, performance was not uniformly better for every target type or operating condition.

Important observations:

- Random Forest performed better overall on nonzero targets.
- Seasonal naive performed substantially better on zero-request targets.
- High sMAPE values were influenced by zero-request hours.
- The Random Forest was not uniformly superior for every individual prediction.
- High-demand evening hours, particularly around hours 21–23, were difficult for the Random Forest.
- Per-hour diagnostic sample sizes were small, generally around four to five observations per hour.

### 8.4 Dataset B MAE Improvement

Random Forest MAE improvement compared with persistence:

| Horizon | Improvement |
| ------- | ----------- |
| 1 hour | 31.81% |
| 6 hours | 46.12% |
| 12 hours | 51.71% |

Random Forest MAE improvement compared with seasonal naive:

| Horizon | Improvement |
| ------- | ----------- |
| 1 hour | 45.03% |
| 6 hours | 5.99% |
| 12 hours | -19.32% |

The negative value at 12 hours indicates that the Random Forest had higher MAE than the seasonal-naive baseline at that horizon.

Therefore, the claim that Random Forest outperformed both baselines should be limited to the aggregate Dataset B MAE/RMSE comparison and should not be interpreted as universal superiority across all subsets.

---

## 9. Dataset B Independently Tuned Feature-Condition Comparison

### 9.1 Ablation Design

The Dataset B ablation compared:

- Full feature set
- Feature set without lag_24

The ablation was conducted using:

```
experiments/forecasting/run_external_ablation.py
```

Unlike Dataset A, Dataset B independently selected the Random Forest hyperparameters for each ablation condition.

Therefore, the Dataset B comparison is a comparison of independently tuned variants rather than a pure fixed-hyperparameter feature ablation.

### 9.2 Authoritative Dataset B Ablation Run

```
results/20260917T152404Z/
```

Comparison file:

```
results/20260917T152404Z/dataset_b_gentd26_ablation/comparison_metrics.csv
```

**Full Feature Configuration**

```
n_estimators = 100
min_samples_leaf = 1
max_depth = None
```

Validation mean MAE:

```
39.5823
```

**Without lag_24 Configuration**

```
n_estimators = 200
min_samples_leaf = 2
max_depth = None
```

Validation mean MAE:

```
36.1140
```

### 9.3 Dataset B Ablation Results

| Horizon | Full Features MAE | Without lag_24 MAE | Change |
| ------- | ------------------ | -------------------- | ------ |
| 1 hour | 22.648889 | 20.217577 | -10.73% |
| 6 hours | 37.963636 | 31.230162 | -17.74% |
| 12 hours | 49.380202 | 39.103786 | -20.81% |

RMSE also decreased for the no-lag_24 condition at all three horizons.

The no-lag_24 configuration achieved lower test MAE in this experiment.

### 9.4 Dataset B Ablation Interpretation

The no-lag_24 condition performed better than the full feature condition in the evaluated Dataset B experiment.

However, the two conditions used independently selected hyperparameters.

Consequently:

- The result is not a pure fixed-hyperparameter feature ablation.
- The improvement cannot be attributed solely to removing lag_24.
- The result does not prove that lag_24 is harmful in general.
- The finding is specific to the evaluated dataset, features, configurations, and experimental procedure.

The Dataset B ablation should be described as an independently tuned feature-condition comparison.

---

## 10. Diagnostic Figures

### 10.1 Dataset A Figures

Dataset A figures are stored under:

```
results/forecast_analysis/figures/
```

Available figures:

- figure_1_mae_by_horizon.png
- figure_2_rf_mae_endpoint_horizon.png
- figure_3_actual_vs_rf_forecast.png
- figure_4_rf_horizon_error.png
- figure_5_rf_error_over_time.png
- figure_6_lag24_ablation.png

These figures cover:

- Aggregate MAE by horizon
- Endpoint-horizon Random Forest MAE
- Actual versus predicted workload
- Horizon-level error
- Error over time
- Lag-24 ablation comparison

### 10.2 Dataset B Figures

Dataset B figures are stored under:

```
results/20260917T145858Z/dataset_b_gentd26/figures/
```

The plotting script is:

```
experiments/forecasting/plot_external_diagnostics.py
```

The script uses the authoritative primary Dataset B run:

```
20260917T145858Z
```

Available figures:

- test_mae_by_horizon.png
- test_mae_rmse_comparison.png
- actual_vs_predicted_1h.png
- actual_vs_predicted_6h.png
- actual_vs_predicted_12h.png
- error_by_hour_1h.png
- error_by_hour_6h.png
- error_by_hour_12h.png
- error_zero_vs_nonzero_1h.png
- error_zero_vs_nonzero_6h.png
- error_zero_vs_nonzero_12h.png
- residual_distribution_1h.png
- residual_distribution_6h.png
- residual_distribution_12h.png

Total Dataset B diagnostic figures:

```
14
```

The figures cover:

- MAE by forecast horizon
- MAE/RMSE baseline comparison
- Actual versus predicted values
- Error by hour
- Zero-target versus nonzero-target error
- Residual distributions

---

## 11. Reproducibility and Artifact Locations

### 11.1 Dataset A Primary Run

```
results/20260910T174657Z/
```

Important artifacts:

- frozen_config.json
- metrics.csv
- predictions.csv
- rf_validation_selection.csv
- run_metadata.json

### 11.2 Dataset A Ablation

```
results/20260910T175101Z/
```

Important artifacts:

- ablation_comparison.csv
- metrics.csv
- predictions.csv
- run_metadata.json

### 11.3 Dataset A Analysis

```
results/forecast_analysis/
```

This directory contains aggregate metrics, endpoint-level analysis, horizon analysis, error summaries, and baseline comparisons.

### 11.4 Dataset B Primary Run

```
results/20260917T145858Z/
```

This run contains Dataset B metadata, validation selection, predictions, metrics, and related artifacts.

### 11.5 Dataset B Ablation

```
results/20260917T152404Z/
```

Comparison file:

```
results/20260917T152404Z/dataset_b_gentd26_ablation/comparison_metrics.csv
```

### 11.6 Forecasting Implementation

```
experiments/forecasting/
```

Important scripts include:

- run_external_forecast.py
- run_external_ablation.py
- plot_external_diagnostics.py

Dataset A forecasting implementation and related scripts are maintained in the same forecasting experiment directory.

---

## 12. Reproducibility Instructions

### 12.1 Environment

The experiments were conducted using the project's Python environment and tracked repository state.

Reproducibility metadata records include:

- Run ID
- Git commit
- Configuration
- Random seed
- Input data hash
- UTC execution timestamp
- Environment/package information

### 12.2 Dataset A

Dataset A experiments use the committed dataset and the corrected forecasting implementation.

The authoritative Dataset A run is:

```
results/20260910T174657Z/
```

The authoritative Dataset A ablation is:

```
results/20260910T175101Z/
```

Do not modify the Dataset A scripts or frozen protocol when reproducing the reported results.

### 12.3 Dataset B

Dataset B requires the raw GenTD26 data to be available locally.

The raw data is intentionally not committed to the repository.

The processed hourly file must be available at:

```
data/processed/dataset_b_candidate/gentd26_hourly_request_counts.csv
```

The primary Dataset B runner is:

```
python -m experiments.forecasting.run_external_forecast
```

The Dataset B diagnostic plotting command is:

```
python -m experiments.forecasting.plot_external_diagnostics
```

The plotting script must reference the authoritative run:

```
20260917T145858Z
```

The Dataset B ablation runner is:

```
python -m experiments.forecasting.run_external_ablation
```

The exact command-line arguments and configuration should be checked against the current script implementation before rerunning an experiment.

### 12.4 Reproducibility Requirements

When reproducing or extending an experiment:

- Record a new run ID.
- Record the current Git commit.
- Record the dataset or input hash.
- Preserve the chronological split.
- Avoid test-set tuning.
- Save validation-selection artifacts.
- Save predictions and metrics.
- Record configuration changes.
- Keep old results intact.
- Treat modified protocols as separate experiments.

---

## 13. Testing Status

### 13.1 External Forecasting Tests

The dedicated external forecasting regression tests passed:

```
3 passed
```

The tests cover selected forecasting behavior, including:

- Past-only persistence evaluation
- Prediction isolation from future actual values
- Rejection of unknown models

### 13.2 Full Repository Test Suite

The full repository test suite passed:

```
10 passed, 4 warnings
```

The tests provide regression coverage for selected behavior.

They do not prove that every possible leakage pathway is impossible.

Testing should be repeated if the forecasting implementation, feature construction, evaluation procedure, or data preparation changes.

---

## 14. Limitations

### 14.1 Dataset A Limitations

Dataset A is a controlled synthetic workload dataset.

Its patterns and injected workload events are not equivalent to independently observed production telemetry.

The following limitations apply:

- The dataset is synthetic.
- The evaluated time period is limited.
- Only five endpoints are included.
- Endpoint behavior may not represent production systems.
- Large workload changes produce larger forecast errors.
- Aggregate performance does not imply uniform accuracy across endpoints.
- The experiment does not establish general superiority of Random Forest for all workloads.
- The lag-24 ablation finding is specific to the evaluated setup.

### 14.2 Dataset B Limitations

Dataset B provides external validation using a real-world GenAI serving trace, but it also has limitations:

- The trace represents a specific serving workload.
- Timestamps are anonymized or shifted.
- The target is constructed through hourly request aggregation.
- Zero-request hours are included in the continuous hourly series.
- The trace has irregular raw inter-event gaps.
- Seasonal patterns may reflect dataset-specific operational behavior.
- High sMAPE values are affected by zero-request hours.
- Seasonal naive performs better on zero-target subsets.
- High-demand evening periods are difficult to forecast.
- Per-hour diagnostic sample sizes are small.
- The Dataset B ablation uses independently selected hyperparameters.
- Results should not be generalized to all GenAI serving systems.

### 14.3 Generalization

The experiments provide evidence for the evaluated datasets and protocols.

They do not establish that:

- Random Forest is the best forecasting model.
- Random Forest will outperform all baselines on every dataset.
- The selected feature set is universally optimal.
- Removing lag_24 is generally beneficial.
- The results apply to all production environments.
- The results demonstrate causal relationships between individual features and forecasting performance.

---

## 15. What Teammates May Claim

The following claims are supported by the completed experiments when appropriately scoped.

### 15.1 Dataset A Claims

Teammates may state that:

- The corrected Random Forest implementation achieved lower aggregate MAE than persistence and seasonal naive at all three evaluated horizons on Dataset A.
- Random Forest achieved lower MAE than persistence in 14 of 15 endpoint-horizon combinations.
- Forecasting performance varied substantially by endpoint.
- /payments had the highest forecasting error and strongest systematic underprediction.
- Removing lag_24 improved aggregate MAE in the fixed-hyperparameter Dataset A ablation.
- Dataset A results are based on a controlled synthetic workload dataset.

### 15.2 Dataset B Claims

Teammates may state that:

- GenTD26 was used as an external real-world validation dataset.
- Random Forest achieved lower aggregate MAE than persistence at all three evaluated horizons.
- Random Forest achieved lower MAE than seasonal naive at the 1-hour and 6-hour horizons, but seasonal naive achieved lower MAE at 12 hours.
- Random Forest achieved lower RMSE than both evaluated baselines at all three horizons.
- Random Forest performed better overall on nonzero targets.
- Seasonal naive performed better on zero-target subsets.
- Zero-request hours influenced sMAPE.
- The no-lag_24 condition achieved lower test MAE in the evaluated Dataset B ablation.
- Dataset B ablation conditions used independently selected hyperparameters.

### 15.3 General Claims

Teammates may state that:

- The experiments use chronological evaluation.
- Model selection is performed using validation data only.
- Multi-step Random Forest forecasting uses recursive predictions.
- Predictions and metrics are saved as machine-readable artifacts.
- Regression tests were used to check selected forecasting behaviors.

---

## 16. What Teammates Should Not Claim

The following claims are not supported by the current experiments.

Do not claim that:

- Random Forest is universally the best forecasting model.
- Random Forest always outperforms persistence or seasonal naive.
- Random Forest is superior for every endpoint, horizon, or target subset.
- The model is production-ready based solely on these experiments.
- Dataset A is production telemetry.
- Dataset B represents all GenAI serving workloads.
- Removing lag_24 universally improves forecasting.
- The Dataset B ablation proves that lag_24 causes worse performance.
- The Dataset B result is a fixed-hyperparameter ablation.
- High sMAPE alone demonstrates poor forecasting quality without considering zero-target behavior.
- The results establish causality.
- The experiments eliminate every possible leakage pathway.
- The model has been validated across multiple independent production environments.
- Dataset A and Dataset B metrics can be directly pooled into one overall score.
- The model's aggregate performance guarantees reliable predictions during sudden workload changes.

Avoid using unsupported phrases such as:

- "Always accurate"
- "Production-ready"
- "Best model"
- "Universal improvement"
- "Guaranteed forecasting accuracy"
- "Zero prediction error"
- "Works for all workloads"

Claims should identify the dataset, forecast horizon, evaluation metric, and experimental conditions whenever relevant.

---

## 17. Recommended Paper Framing

### 17.1 Dataset A

Dataset A should be described as a controlled synthetic experiment used to evaluate the forecasting pipeline, feature construction, baseline comparison, and recursive forecasting implementation.

The results demonstrate that the Random Forest achieved lower aggregate MAE than the evaluated temporal baselines within the Dataset A setup.

The synthetic nature of the dataset should be stated clearly.

### 17.2 Dataset B

Dataset B should be described as an external validation experiment using the GenTD26 real-world GenAI serving trace.

The results provide evidence about model behavior on a separate workload trace.

Dataset B should not be described as proof of universal production generalization.

The presence of zero-request hours, the difference between zero and nonzero target performance, and the independently tuned ablation should be disclosed.

### 17.3 Ablation Reporting

The two ablation experiments should be reported differently:

| Dataset | Ablation Type |
| ------- | -------------- |
| Dataset A | Fixed-hyperparameter feature ablation |
| Dataset B | Independently tuned feature-condition comparison |

The Dataset B ablation should not be described as a pure measurement of the isolated contribution of lag_24.

---

## 18. Authoritative Files and Runs

### Dataset A

Primary run:

```
results/20260910T174657Z/
```

Ablation:

```
results/20260910T175101Z/
```

Analysis:

```
results/forecast_analysis/
```

Protocol:

```
docs/forecasting_frozen_protocol.md
```

Results:

```
docs/forecasting_results.md
```

### Dataset B

Primary run:

```
results/20260917T145858Z/
```

Ablation:

```
results/20260917T152404Z/
```

Results documentation:

```
docs/dataset_b_forecasting_results.md
```

Figures:

```
results/20260917T145858Z/dataset_b_gentd26/figures/
```

External forecasting runner:

```
experiments/forecasting/run_external_forecast.py
```

External ablation runner:

```
experiments/forecasting/run_external_ablation.py
```

External diagnostics script:

```
experiments/forecasting/plot_external_diagnostics.py
```

External forecasting tests:

```
tests/test_external_forecasting.py
```

---

## 19. Final Handoff Summary

The forecasting work is complete for both Dataset A and Dataset B.

Dataset A provides controlled synthetic evaluation with a corrected recursive Random Forest implementation, temporal baselines, error analysis, and a fixed-hyperparameter lag-24 ablation.

Dataset B provides separate external validation using the GenTD26 real-world GenAI serving trace, including temporal baseline comparison, zero/nonzero error analysis, diagnostic figures, and an independently tuned lag-24 feature-condition comparison.

The final paper should:

- Report Dataset A and Dataset B separately.
- Use the authoritative run IDs.
- Preserve the distinction between fixed and independently tuned ablations.
- Report limitations and zero-target behavior.
- Avoid universal claims about model superiority.
- Use committed metrics and predictions as the source of numerical results.
- Preserve reproducibility metadata for all reported numbers.

---

## 20. Final Checklist

Before submitting the research paper, verify the following:

- Dataset A and Dataset B results are reported separately.
- All reported metrics match the committed CSV artifacts.
- Dataset A's fixed-hyperparameter ablation is clearly distinguished from Dataset B's independently tuned ablation.
- The Dataset B zero-target and nonzero-target analysis is included where relevant.
- The synthetic nature of Dataset A is disclosed.
- Dataset B's source and preprocessing procedure are documented.
- The temporal split and validation-only selection procedure are described.
- No test-set tuning is reported.
- All paper figures correspond to the authoritative experiment runs.
- Run IDs and Git commits are recorded for reported results.
- The forecasting pipeline can be rerun by at least one teammate.
- Weak results and limitations are retained rather than omitted.
- No unsupported claims of universal model superiority are included.

---

## 21. Ownership and Handoff Notes

The forecasting workstream includes:

- Dataset preparation and validation
- Temporal split construction
- Baseline implementation
- Random Forest forecasting
- Recursive forecasting evaluation
- Error analysis
- Feature ablation
- External Dataset B validation
- Diagnostic figure generation
- Reproducibility documentation

Any future changes to the forecasting pipeline should be documented as new experiments.

Changes to the following should trigger a new run and updated metadata:

- Dataset preprocessing
- Target construction
- Feature set
- Temporal split
- Model configuration
- Hyperparameter selection
- Evaluation horizon
- Evaluation metric
- Recursive forecasting procedure
- Baseline implementation

Existing results should not be overwritten without preserving the original run and documenting the reason for the change.

The current authoritative results should remain reproducible from the committed code, configuration, data preparation procedure, and saved experiment artifacts.