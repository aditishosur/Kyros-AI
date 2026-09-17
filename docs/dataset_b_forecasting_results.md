
# Dataset B Forecasting Results: GenTD26

## 1. Dataset Overview

Dataset B uses the GenTD26 real production GenAI serving trace from Alibaba's cluster-trace repository.

- Dataset: GenTD26
- Source: Alibaba cluster-trace-v2026-GenAI
- Selected trace: `lora_request_trace.csv`
- Target: Hourly aggregate request count
- Raw observations: 26,823
- Continuous hourly bins: 554
- Nonzero hourly bins: 370
- Zero-request hourly bins: 184
- Temporal coverage: Approximately 23 days
- Request types: TXT_2_IMG, IMG_2_IMG, INPAINTING

The timestamps are anonymized or shifted. They are used for temporal ordering and aggregation rather than interpreted as actual calendar time.

No-event hours were represented as zero request counts. No smoothing or interpolation was applied.

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

## 3. Evaluation Protocol

The hourly series was divided chronologically into:

| Split | Duration |
|---|---:|
| Training | 332 hours |
| Validation | 111 hours |
| Test | 111 hours |

The split was chronological, with no random shuffling.

The Random Forest configuration was selected using validation data only. The final model was refitted using the training and validation portions before evaluation on the held-out test period.

Test observations were used as rolling history for subsequent forecast origins, but future target values were not used to construct earlier predictions.

## 4. Experiment Metadata

- Run ID: `20260917T143019Z`
- Git commit: `8b6b683f80850ad2e0ed6b96d3adaf541e621625`
- Input SHA256: `ff73b8665297f8bac27711db72540c9bffe387ebd741b4f0805651d29e4b7e94`
- Random state: inherited from the forecasting experiment configuration
- Selected Random Forest configuration:
  - `n_estimators=100`
  - `min_samples_leaf=1`
  - `max_depth=None`

## 5. Test Results

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

## 6. Initial Findings

The Random Forest produced lower overall MAE and RMSE than both baselines across all three evaluated horizons in this test run.

Relative to Persistence, the Random Forest's MAE improvement was:

- 1 hour: 31.81%
- 6 hours: 46.12%
- 12 hours: 51.71%

Relative to Seasonal Naive, the Random Forest's MAE improvement was:

- 1 hour: 45.03%
- 6 hours: 5.99%
- 12 hours: -19.32%

The Seasonal Naive baseline performed substantially better on zero-request targets. The Random Forest performed better on nonzero targets in the examined test predictions.

These findings should not be interpreted as universal superiority. Performance varies according to demand level, time of day, forecast horizon, and whether the target request count is zero.

## 7. Limitations

- The dataset contains recurring zero-request periods.
- The hourly series includes long zero-demand intervals.
- Per-target-hour sample sizes are small, generally approximately four to five observations.
- The timestamps are anonymized or shifted.
- sMAPE is difficult to interpret when actual request counts are zero or close to zero.
- The dataset covers approximately 23 days, limiting the amount of repeated temporal evidence.
- The results represent one held-out temporal evaluation and should not be generalized to all production workloads.

## 8. Reproducibility Artifacts

The experiment generated:

- Run metadata
- Validation model-selection metrics
- Test metrics
- Test predictions

Expected artifact locations:

```text
results/20260917T143019Z/
└── dataset_b_gentd26/
    ├── metadata/
    │   └── run_metadata.json
    ├── metrics/
    │   ├── rf_validation_selection.csv
    │   └── test_metrics.csv
    └── predictions/
        └── test_predictions.csv
```