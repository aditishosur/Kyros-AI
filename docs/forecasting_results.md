# Forecasting Results

## 1. Overview

This document reports the final results of the Dataset A workload forecasting experiment.

The forecasting task predicts hourly `request_count` for five API endpoints at three forecast horizons:

- 1 hour
- 6 hours
- 12 hours

The reported results are based on the **corrected recursive forecasting implementation**. Earlier runs generated before the recursive timestamp/feature alignment correction are superseded and are not used in the reported results.

---

## 2. Final Random Forest Configuration

The Random Forest configuration was selected using the validation set only.

The selected configuration was:

```text
n_estimators = 200
min_samples_leaf = 2
max_depth = None
random_state = 42
```

The selected configuration achieved a validation mean MAE of:

```text
43.0845
```

After configuration selection, the model configuration was frozen before held-out test evaluation.

---

## 3. Dataset A Test Performance

The final Random Forest achieved the following aggregate mean MAE across all five endpoints:

| Forecast Horizon | Random Forest MAE |
| ---------------- | ----------------: |
| 1 hour           |            50.807 |
| 6 hours          |            66.048 |
| 12 hours         |            69.729 |

The corresponding persistence baseline results were:

| Forecast Horizon | Persistence MAE |
| ---------------- | --------------: |
| 1 hour           |          55.255 |
| 6 hours          |         118.625 |
| 12 hours         |         170.916 |

The seasonal-naive baseline results were:

| Forecast Horizon | Seasonal Naive MAE |
| ---------------- | -----------------: |
| 1 hour           |            115.098 |
| 6 hours          |            118.276 |
| 12 hours         |            113.320 |

---

## 4. Comparison with Temporal Baselines

The Random Forest outperformed both temporal baselines at all three evaluated forecast horizons.

Compared with persistence, the Random Forest reduced mean MAE by:

| Horizon  | Improvement vs Persistence |
| -------- | -------------------------: |
| 1 hour   |                      8.05% |
| 6 hours  |                     44.32% |
| 12 hours |                     59.20% |

Across the 15 endpoint-horizon combinations, the Random Forest achieved lower MAE than persistence in:

```text
14 / 15
```

cases.

The only exception was `/payments` at the 1-hour horizon:

- Persistence MAE: **52.255**
- Random Forest MAE: **71.416**

Thus, although the Random Forest performed better in aggregate, persistence remained competitive for this specific endpoint-horizon combination.

---

## 5. Random Forest Performance by Endpoint

The final Random Forest MAE values were:

| Endpoint     |     1h |     6h |     12h |
| ------------ | -----: | -----: | ------: |
| `/identity`  | 27.263 | 27.703 |  25.246 |
| `/inventory` | 37.070 | 44.787 |  40.717 |
| `/orders`    | 51.602 | 71.350 |  74.601 |
| `/payments`  | 71.416 | 97.572 | 122.199 |
| `/search`    | 66.683 | 88.830 |  85.881 |

`/identity` had the lowest forecasting error across the evaluated endpoints.

`/payments` had the highest forecasting error, particularly at longer horizons.

---

## 6. Error Analysis

The final Random Forest produced 825 test prediction records:

```text
55 forecast origins × 5 endpoints × 3 horizons = 825
```

Across these predictions, the overall MAE was:

```text
62.195
```

Endpoint-level error statistics were:

| Endpoint     |    MAE |    RMSE | Mean Error |
| ------------ | -----: | ------: | ---------: |
| `/payments`  | 97.062 | 132.076 |    +51.282 |
| `/search`    | 80.465 | 106.142 |    +12.973 |
| `/orders`    | 65.851 |  85.433 |     +8.975 |
| `/inventory` | 40.858 |  53.505 |     -7.139 |
| `/identity`  | 26.737 |  33.855 |     +1.535 |

Mean error is defined as:

```text
actual - prediction
```

Therefore, a positive mean error indicates systematic underprediction.

The `/payments` endpoint showed the strongest systematic underprediction.

---

## 7. Error by Forecast Horizon

Aggregate Random Forest error by horizon was:

| Horizon  |    MAE |   RMSE | Mean Error |
| -------- | -----: | -----: | ---------: |
| 1 hour   | 50.807 | 74.649 |     +3.507 |
| 6 hours  | 66.048 | 93.101 |    +12.856 |
| 12 hours | 69.729 | 98.846 |    +24.213 |

MAE and RMSE increased as the forecast horizon increased.

The positive mean error also increased with horizon, indicating greater aggregate underprediction at longer horizons.

---

## 8. Largest Forecast Errors

The largest individual absolute errors in the final Random Forest test predictions included:

### `/search`

- Timestamp: `2026-08-01 14:00 UTC`
- Horizon: 1 hour
- Actual: `1119`
- Prediction: `703.635`
- Absolute error: `415.365`
- APE: `37.12%`

### `/payments`

- Timestamp: `2026-08-04 04:00 UTC`
- Horizon: 12 hours
- Actual: `756`
- Prediction: `367.765`
- Absolute error: `388.235`
- APE: `51.35%`

### `/search`

- Timestamp: `2026-08-03 12:00 UTC`
- Horizon: 12 hours
- Actual: `1012`
- Prediction: `668.622`
- Absolute error: `343.378`
- APE: `33.93%`

These cases show that large workload changes can result in substantially larger forecast errors.

---

## 9. Lag-24 Feature Ablation

A controlled feature ablation compared:

1. `RF_FullFeatures`
2. `RF_WithoutLag24`

The Random Forest configuration was kept fixed for both conditions:

```text
n_estimators = 200
min_samples_leaf = 2
max_depth = None
random_state = 42
```

No additional hyperparameter selection was performed for the ablation.

### Aggregate Ablation Results

| Horizon  | Full Features MAE | Without `lag_24` MAE |   Change |
| -------- | ----------------: | -------------------: | -------: |
| 1 hour   |            50.807 |               50.452 |  -0.527% |
| 6 hours  |            66.048 |               60.210 |  -8.751% |
| 12 hours |            69.729 |               61.903 | -10.770% |

Removing `lag_24` improved aggregate MAE at all three evaluated horizons.

Across the 15 endpoint-horizon combinations:

```text
14 / 15
```

cases improved after removing `lag_24`.

The only case that became worse was `/orders` at the 1-hour horizon, where MAE increased by approximately **1.21%**.

### Interpretation

On Dataset A, removing the 24-hour lag feature did not degrade forecasting performance and generally improved MAE across the evaluated endpoints and horizons.

This finding is specific to Dataset A, the evaluated feature set, the Random Forest configuration, and the experimental procedure. It does not establish that 24-hour lag features are generally unnecessary for workload forecasting.

---

## 10. Key Findings

The Dataset A experiment produced four primary findings:

1. **Random Forest outperformed both simple temporal baselines in aggregate at all three forecast horizons.**

2. **The advantage over persistence increased with forecast horizon**, from 8.05% lower MAE at 1 hour to 59.20% lower MAE at 12 hours.

3. **Forecasting performance varied substantially by endpoint.** `/identity` was the easiest endpoint to forecast, while `/payments` produced the largest errors and strongest systematic underprediction.

4. **Removing `lag_24` did not degrade performance in this experiment and generally improved it**, particularly at the 6-hour and 12-hour horizons.

---

## 11. Interpretation and Limitations

The results support the research question on the controlled synthetic Dataset A:

> **Can workload forecasts beat simple temporal baselines?**

For this dataset and experimental setup, the answer is yes. The Random Forest achieved lower aggregate MAE than both persistence and seasonal-naive baselines at 1-hour, 6-hour, and 12-hour horizons.

However, the results should not be generalized beyond the evaluated data without further validation.

Dataset A is a controlled synthetic workload dataset. Its temporal patterns and injected workload events are therefore not equivalent to independently observed production telemetry.

The endpoint-level differences and large errors during workload changes also show that strong aggregate performance does not imply uniformly accurate forecasts for every endpoint or operating condition.

For these reasons, an independent real-world Dataset B is required before making broader claims about forecasting performance.

---

## 12. Reproducibility Artifacts

### Primary corrected forecasting run

```text
results/20260910T174657Z/
```

Contains:

- `frozen_config.json`
- `metrics.csv`
- `predictions.csv`
- `rf_validation_selection.csv`
- `run_metadata.json`

### Corrected feature ablation

```text
results/20260910T175101Z/
```

Contains:

- `ablation_comparison.csv`
- `metrics.csv`
- `predictions.csv`
- `run_metadata.json`

### Error analysis

```text
results/forecast_analysis/
```

Contains the generated aggregate metrics, endpoint-level analysis, horizon analysis, error summaries, and baseline comparisons.

### Figures

```text
results/forecast_analysis/figures/
```

Contains:

figure_1_mae_by_horizon.png
figure_2_rf_mae_endpoint_horizon.png
figure_3_actual_vs_rf_forecast.png
figure_4_rf_horizon_error.png
figure_5_rf_error_over_time.png
figure_6_lag24_ablation.png

### Implementation

Forecasting experiment code:

```text
experiments/forecasting/
```

Forecasting regression tests:

```text
tests/test_forecasting.py
```

The targeted forecasting tests pass:

```text
3 passed
```

The full repository test suite passes:

```text
7 passed
```

---

## 13. Final Dataset A Status

**Dataset A forecasting: COMPLETE**

The corrected implementation, validation, held-out test evaluation, ablation, error analysis, predictions, metrics, and figures have all been generated and verified.

Earlier forecasting runs produced before the recursive feature/timestamp alignment correction are superseded and should not be used for reporting.

### Dataset B

**Real-data validation: PENDING**

Dataset B has not yet been incorporated into these results. Its selection and evaluation will be documented separately after the dataset has been confirmed and its schema, temporal resolution, target mapping, and licensing have been validated.