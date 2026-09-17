
# Dataset B Forecasting Results: GenTD26

## 1. Dataset Overview

Dataset B uses the GenTD26 real production GenAI serving trace from Alibaba's cluster-trace repository.

- **Dataset:** GenTD26
- **Source:** Alibaba cluster-trace-v2026-GenAI
- **Selected trace:** `lora_request_trace.csv`
- **Target:** Hourly aggregate request count
- **Raw observations:** 26,823
- **Continuous hourly bins:** 554
- **Nonzero hourly bins:** 370
- **Zero-request hourly bins:** 184
- **Temporal coverage:** Approximately 23 days
- **Request types:** TXT_2_IMG, IMG_2_IMG, INPAINTING

The timestamps are anonymized or shifted. They are used for temporal ordering and aggregation rather than interpreted as actual calendar time.

The hourly series was constructed using a continuous calendar-hour index. Hours with no observed requests were represented as zero request counts. No smoothing or interpolation was applied.

The dataset contains recurring zero-request periods, including a recurring zero-demand period around 12:00 in the observed timestamp sequence. No causal explanation is inferred from this pattern.

---

## 2. Forecasting Objective

The experiment evaluates whether machine-learning-based workload forecasts improve upon simple temporal baselines.

Models evaluated:

1. Persistence
2. Seasonal Naive with a 24-hour seasonal period
3. Random Forest Regressor

Forecast horizons:

- 1 hour
- 6 hours
- 12 hours

Primary metrics:

- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)

Secondary metric:

- Symmetric Mean Absolute Percentage Error (sMAPE)

The primary research question is:

> Can workload forecasts beat simple temporal baselines?

---

## 3. Evaluation Protocol

The hourly series was divided chronologically into:

| Split | Duration | Requests |
|---|---:|---:|
| Training | 332 hours | 13,865 |
| Validation | 111 hours | 7,076 |
| Test | 111 hours | 5,882 |

The split was chronological, with no random shuffling.

The Random Forest configuration was selected using validation data only. The final model was refitted using the training and validation portions before evaluation on the held-out test period.

Rolling-origin evaluation was used for the test period. Test observations may become available in the forecasting history for subsequent origins, but future target values were not used to construct earlier predictions.

The evaluation uses the continuous hourly series, including zero-request hours.

---

## 4. Primary Experiment Metadata

The authoritative primary Dataset B run is:

```text
Run ID: 20260917T145858Z
```

The experiment uses the GenTD26 aggregate hourly request-count series.

Selected Random Forest configuration:

```text
n_estimators = 100
min_samples_leaf = 1
max_depth = None
```

The configuration was selected using validation performance only.

The experiment records run metadata, model-selection metrics, test metrics, and test predictions.

Primary result directory:

```text
results/20260917T145858Z/
```

---

## 5. Test Results

The following results are from the authoritative primary Dataset B run.

| Model | Horizon | MAE | RMSE | sMAPE |
|---|---:|---:|---:|---:|
| Persistence | 1h | 33.212 | 68.411 | 86.164 |
| Persistence | 6h | 70.455 | 117.656 | 152.336 |
| Persistence | 12h | 102.253 | 151.877 | 162.876 |
| Random Forest | 1h | 22.649 | 39.998 | 95.227 |
| Random Forest | 6h | 37.964 | 64.067 | 111.220 |
| Random Forest | 12h | 49.380 | 73.776 | 112.851 |
| Seasonal Naive | 1h | 41.202 | 79.539 | 91.677 |
| Seasonal Naive | 6h | 40.384 | 79.347 | 93.096 |
| Seasonal Naive | 12h | 41.384 | 79.711 | 94.940 |

Each model-horizon combination contains 99 test predictions.

---

## 6. Comparison with Temporal Baselines

The Random Forest produced lower overall MAE and RMSE than both baselines across all three evaluated horizons in the primary test evaluation.

### 6.1 Comparison with Persistence

The Random Forest's relative MAE improvement over persistence was:

| Horizon | RF MAE | Persistence MAE | Improvement |
|---|---:|---:|---:|
| 1h | 22.649 | 33.212 | 31.81% |
| 6h | 37.964 | 70.455 | 46.12% |
| 12h | 49.380 | 102.253 | 51.71% |

### 6.2 Comparison with Seasonal Naive

The Random Forest's relative MAE improvement over seasonal naive was:

| Horizon | RF MAE | Seasonal Naive MAE | Improvement |
|---|---:|---:|---:|
| 1h | 22.649 | 41.202 | 45.03% |
| 6h | 37.964 | 40.384 | 5.99% |
| 12h | 49.380 | 41.384 | -19.32% |

At the 12-hour horizon, seasonal naive achieved lower MAE than the Random Forest.

These aggregate results do not establish universal superiority of the Random Forest. Performance varies according to demand level, time of day, forecast horizon, and whether the target request count is zero.

---

## 7. Zero-Request and Nonzero-Request Behavior

The error analysis identified different model behavior across zero-request and nonzero-request targets.

- The Random Forest performed better on nonzero targets in the examined test predictions.
- Seasonal naive performed substantially better on zero-request targets.
- The Random Forest achieved lower aggregate MAE and RMSE across the evaluated horizons.
- High sMAPE values are influenced by zero-request or near-zero actual values.

This indicates that aggregate metrics alone do not fully describe model behavior across different demand conditions.

The Random Forest should therefore not be described as uniformly superior across every target condition.

---

## 8. Error Analysis by Time of Day

The per-hour error analysis showed that high-demand evening periods, particularly hours 21–23 in the observed timestamp sequence, were difficult for the Random Forest.

Low-demand and zero-request periods showed stronger performance from the seasonal-naive baseline in the examined predictions.

Per-hour sample sizes were small, generally approximately four to five observations per hour-of-day category. Therefore, these patterns should be treated as descriptive observations rather than definitive conclusions about time-of-day behavior.

The timestamps are anonymized or shifted, so the observed hour labels should not be interpreted as verified local or UTC operating hours.

---

## 9. Mean Prediction Behavior

The mean predictions across the test evaluation were:

| Model | 1h | 6h | 12h |
|---|---:|---:|---:|
| Persistence | 58.02 | — | — |
| Random Forest | 59.95 | 79.68 | 91.19 |
| Seasonal Naive | 77.81 | 76.98 | 77.05 |

The mean prediction values are descriptive and should not be interpreted as evidence of overall model superiority.

---

## 10. Feature Ablation

A feature ablation compared the following Random Forest feature sets:

1. `RF_FullFeatures`
2. `RF_WithoutLag24`

The ablation was conducted using the Dataset B external forecasting runner.

Unlike the original Dataset A ablation, the Dataset B variants underwent independent validation-only hyperparameter selection.

Consequently, this comparison represents a comparison of two tuned feature configurations rather than a pure fixed-hyperparameter feature ablation.

### 10.1 Ablation Metadata

Authoritative ablation run:

```text
20260917T152404Z
```

The selected configurations were:

| Variant | `n_estimators` | `min_samples_leaf` | `max_depth` |
|---|---:|---:|---|
| Full features | 100 | 1 | None |
| Without `lag_24` | 200 | 2 | None |

Validation mean MAE:

| Variant | Validation Mean MAE |
|---|---:|
| Full features | 39.5823 |
| Without `lag_24` | 36.1140 |

### 10.2 Test Ablation Results

| Variant | Horizon | MAE | RMSE | sMAPE |
|---|---:|---:|---:|---:|
| Full features | 1h | 22.649 | 39.998 | 95.227 |
| Full features | 6h | 37.964 | 64.067 | 111.220 |
| Full features | 12h | 49.380 | 73.776 | 112.851 |
| Without `lag_24` | 1h | 20.218 | 35.276 | 92.295 |
| Without `lag_24` | 6h | 31.230 | 54.459 | 104.238 |
| Without `lag_24` | 12h | 39.104 | 61.723 | 97.086 |

### 10.3 Ablation Changes

The MAE changes for the `RF_WithoutLag24` variant relative to the full-feature variant were:

| Horizon | MAE Change |
|---|---:|
| 1h | -10.73% |
| 6h | -17.74% |
| 12h | -20.81% |

RMSE was also lower for the `RF_WithoutLag24` variant at all three horizons in this ablation run.

### 10.4 Ablation Interpretation

Removing `lag_24` produced lower test MAE and RMSE in the evaluated Dataset B ablation.

However, because the two variants were independently tuned, the results do not isolate the causal contribution of the `lag_24` feature alone.

This finding is specific to:

- The GenTD26 dataset
- The evaluated feature configurations
- The validation-selection procedure
- The Random Forest model
- The forecasting horizons
- The temporal evaluation protocol

It does not establish that `lag_24` is generally harmful or unnecessary for workload forecasting.

---

## 11. Diagnostic Figures

The primary Dataset B diagnostic figures are stored at:

```text
results/20260917T145858Z/dataset_b_gentd26/figures/
```

The figure set includes:

- `test_mae_by_horizon.png`
- `test_mae_rmse_comparison.png`
- `actual_vs_predicted_1h.png`
- `actual_vs_predicted_6h.png`
- `actual_vs_predicted_12h.png`
- `error_by_hour_1h.png`
- `error_by_hour_6h.png`
- `error_by_hour_12h.png`
- `error_zero_vs_nonzero_1h.png`
- `error_zero_vs_nonzero_6h.png`
- `error_zero_vs_nonzero_12h.png`
- `residual_distribution_1h.png`
- `residual_distribution_6h.png`
- `residual_distribution_12h.png`

These figures support comparison of model errors across horizons, time-of-day categories, zero/nonzero targets, and residual distributions.

---

## 12. Key Findings

The Dataset B experiment produced the following findings:

1. The Random Forest achieved lower aggregate MAE and RMSE than persistence and seasonal naive at all three evaluated horizons in the primary test evaluation.

2. Relative to persistence, the Random Forest reduced MAE by 31.81% at 1 hour, 46.12% at 6 hours, and 51.71% at 12 hours.

3. Relative to seasonal naive, the Random Forest achieved lower MAE at 1 hour and 6 hours, while seasonal naive achieved lower MAE at 12 hours.

4. Seasonal naive performed substantially better on zero-request targets, while the Random Forest performed better on nonzero targets in the examined test predictions.

5. High sMAPE values were influenced by zero-request and near-zero actual values.

6. Removing `lag_24` produced lower MAE and RMSE in the evaluated Dataset B ablation, but the independently tuned configurations prevent this from being interpreted as a pure feature-isolation result.

7. The dataset's anonymized timestamps, limited temporal coverage, recurring zero-request periods, and small per-hour sample sizes limit the scope of the conclusions.

---

## 13. Limitations

The results have the following limitations:

- The dataset contains recurring zero-request periods.
- The hourly series includes long zero-demand intervals.
- Per-target-hour sample sizes are small, generally approximately four to five observations.
- The timestamps are anonymized or shifted.
- sMAPE is difficult to interpret when actual request counts are zero or close to zero.
- The dataset covers approximately 23 days, limiting the amount of repeated temporal evidence.
- The evaluation represents one held-out temporal test period.
- The dataset is an external validation source but does not establish performance across all production workloads.
- The feature ablation uses independently selected configurations, so it does not isolate the effect of `lag_24` independently of hyperparameter selection.
- The results should not be generalized to all production workloads or deployment conditions.

---

## 14. Reproducibility Artifacts

### Primary Dataset B run

```text
results/20260917T145858Z/
```

The primary run contains:

- Run metadata
- Validation model-selection metrics
- Test metrics
- Test predictions

### Dataset B ablation

```text
results/20260917T152404Z/
```

The ablation comparison is available at:

```text
results/20260917T152404Z/dataset_b_gentd26_ablation/comparison_metrics.csv
```

The ablation run contains the results for the full-feature and `RF_WithoutLag24` variants.

### Diagnostic figures

```text
results/20260917T145858Z/dataset_b_gentd26/figures/
```

### Implementation

The external forecasting implementation is located under:

```text
experiments/forecasting/
```

The external forecasting runner is:

```text
experiments/forecasting/run_external_forecast.py
```

The external ablation runner is:

```text
experiments/forecasting/run_external_ablation.py
```

The diagnostic plotting script is:

```text
experiments/forecasting/plot_external_diagnostics.py
```

---

## 15. Validation and Testing

The external forecasting tests cover:

1. Past-only behavior for the persistence model.
2. Prediction stability when future actual values are modified.
3. Rejection of unknown model names.

The dedicated external forecasting tests passed:

```text
3 passed
```

The full repository test suite passed:

```text
10 passed, 4 warnings
```

These tests provide targeted checks for selected leakage and evaluation behaviors. They do not prove that every possible leakage pathway is absent.

---

## 16. Final Dataset B Status

**Dataset B forecasting: COMPLETE**

The GenTD26 dataset was processed into a continuous hourly aggregate request-count series. The primary forecasting evaluation, validation-only model selection, held-out test evaluation, ablation, diagnostic figures, and reproducibility artifacts have been generated.

The results provide external validation evidence for the forecasting research question. They should be interpreted together with Dataset A results and the documented limitations.

The Random Forest demonstrated lower aggregate error than both baselines in the primary Dataset B test evaluation, but seasonal naive remained stronger for zero-request targets and achieved lower aggregate MAE at the 12-hour horizon.

The findings do not establish universal superiority of any forecasting model across all demand patterns, datasets, horizons, or production workloads.