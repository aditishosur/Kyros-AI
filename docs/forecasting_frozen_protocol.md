# Forecasting Frozen Protocol

## 1. Research Question

**Can workload forecasts beat simple temporal baselines?**

The forecasting experiment evaluates whether a Random Forest regression model can improve workload forecasting accuracy over simple temporal baselines on the controlled synthetic Dataset A.

The primary workload target is:

- `request_count`

Forecasting is evaluated for:

- 1-hour ahead
- 6-hour ahead
- 12-hour ahead

---

## 2. Dataset A

Dataset A is the controlled synthetic API telemetry dataset:

`data/api_logs.csv`

The dataset contains:

- 1,680 rows
- 5 API endpoints
- 336 unique hourly timestamps
- 336 observations per endpoint

Endpoints:

- `/payments`
- `/orders`
- `/inventory`
- `/identity`
- `/search`

Relevant fields include:

- `timestamp`
- `endpoint`
- `request_count`
- `response_time_ms`
- `cpu_usage`
- `db_latency_ms`
- `status_code`

The forecasting target is hourly `request_count`.

---

## 3. Temporal Resolution and Ordering

All forecasting experiments operate at hourly temporal resolution.

Observations are ordered chronologically by timestamp.

No random train/test shuffling is permitted.

All temporal splits and evaluation procedures preserve chronological order.

---

## 4. Train / Validation / Test Split

Dataset A contains 336 unique hourly timestamps.

The frozen split is:

| Split | Timestamps | Rows |
|---|---:|---:|
| Train | 202 | 1,010 |
| Validation | 67 | 335 |
| Test | 67 | 335 |

The temporal ranges are:

### Train

`2026-07-21 06:00:00 UTC` → `2026-07-29 15:00:00 UTC`

### Validation

`2026-07-29 16:00:00 UTC` → `2026-08-01 10:00:00 UTC`

### Test

`2026-08-01 11:00:00 UTC` → `2026-08-04 05:00:00 UTC`

The split is chronological and non-overlapping.

The test set is not used for hyperparameter selection.

---

## 5. Forecasting Features

The frozen Random Forest feature set is:

- `hour`
- `day_of_week`
- `lag_1`
- `lag_3`
- `lag_6`
- `lag_24`
- `rolling_mean_6`
- `rolling_mean_24`

Calendar features are derived from the timestamp being forecast.

Lag features use only observations available before the forecast timestamp.

Rolling features are calculated from shifted historical observations and therefore do not include the value being forecast.

---

## 6. Recursive Forecasting Protocol

Multi-step Random Forest forecasts are generated recursively.

For each forecast step:

1. Determine the next timestamp after the latest available observation.
2. Construct a temporary feature row at that exact next timestamp.
3. Calculate its calendar features from the next timestamp.
4. Calculate lag and rolling features using only observations available before that timestamp.
5. Generate the prediction.
6. Append the generated prediction to the working history.
7. Use that generated prediction when constructing features for subsequent forecast steps.

Future observed values are never used to construct features for an earlier forecast step.

For example, when forecasting `t+1`:

- the feature-row timestamp is `t+1`
- calendar features correspond to `t+1`
- `lag_1` corresponds to `y(t)`
- `lag_3` corresponds to `y(t-2)`
- and so on.

This recursive implementation is covered by targeted regression tests in:

`tests/test_forecasting.py`

---

## 7. Leakage Prevention

The forecasting protocol prohibits future-data leakage.

Specifically:

- Future test observations are not used during RF hyperparameter selection.
- Future observations are not used when constructing forecast features.
- Rolling statistics use past observations only.
- Recursive forecast steps use generated predictions rather than future actual values.
- The test set remains held out until the forecasting configuration is frozen.

Test isolation is explicitly verified by the experiment pipeline.

---

## 8. Baselines

Two temporal baselines are required.

### 8.1 Persistence

The persistence baseline predicts the next workload using the most recently observed workload value.

### 8.2 Seasonal Naive

The seasonal-naive baseline uses the workload from the corresponding 24-hour seasonal position.

These baselines are evaluated at the same forecasting horizons as the Random Forest model.

---

## 9. Random Forest Model

The forecasting model is:

`sklearn.ensemble.RandomForestRegressor`

A small validation-only hyperparameter grid is used.

Candidate configurations:

| `n_estimators` | `min_samples_leaf` | `max_depth` |
|---:|---:|---|
| 100 | 1 | None |
| 140 | 2 | None |
| 200 | 2 | None |
| 140 | 4 | None |
| 140 | 2 | 10 |

The configuration is selected using validation performance only.

The test set is not used for configuration selection.

---

## 10. Frozen Random Forest Configuration

The selected configuration is:

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

After selection, the configuration is frozen for held-out test evaluation.

---

## 11. Final Test Evaluation

After the configuration is frozen, the Random Forest is refit using the available training and validation observations.

The final model is then evaluated on the held-out test period.

Forecast horizons:

- 1 hour
- 6 hours
- 12 hours

The same test period and evaluation procedure are applied to the temporal baselines.

---

## 12. Evaluation Metrics

The primary evaluation metric is:

- Mean Absolute Error (MAE)

Secondary metrics include:

- Root Mean Squared Error (RMSE)
- sMAPE, where applicable
- R², where applicable

MAE is the primary metric used for model comparison because it provides an interpretable measure of average absolute workload prediction error.

---

## 13. Rolling-Origin Evaluation

Evaluation uses rolling forecast origins within the appropriate temporal split.

For each origin:

1. The available historical observations are used as the forecasting history.
2. A recursive forecast is generated for the required horizon.
3. Forecasts are compared with the corresponding future observations.
4. Absolute errors are recorded.

The final test evaluation contains:

- 55 valid forecast origins
- 5 endpoints
- 3 forecast horizons

for a total of:

```text
55 × 5 × 3 = 825
```

RF test prediction records.

---

## 14. Feature Ablation

A single feature ablation is performed after the main configuration is frozen.

The two conditions are:

1. `RF_FullFeatures`
2. `RF_WithoutLag24`

The Random Forest hyperparameters remain frozen between conditions.

No additional hyperparameter selection is performed for the ablation.

Both conditions are evaluated on the same held-out test period using the same horizons and evaluation procedure.

The purpose of the ablation is to assess the contribution of the 24-hour lag feature within this experimental setup.

---

## 15. Reproducibility

Each experiment records reproducibility metadata including:

- run ID
- Git commit
- configuration
- random seed
- input data hash
- UTC execution timestamp
- environment/package information

Forecast predictions and evaluation metrics are saved as machine-readable CSV files.

The forecasting implementation and tests are maintained under:

`experiments/forecasting/`

and

`tests/test_forecasting.py`

---

## 16. Frozen Experimental Boundaries

The following are explicitly outside the frozen forecasting experiment:

- deep learning forecasting models
- LLM-based forecasting
- RAG-based forecasting
- UI-based evaluation
- tuning on the held-out test set
- random temporal splits
- future-data leakage
- undocumented changes to the evaluation procedure

Any future forecasting model or feature experiment must be treated as a separate experiment rather than silently modifying the frozen protocol.

---

## 17. Authoritative Experiment Runs

Corrected Dataset A Random Forest experiment:

results/20260910T174657Z/

Corrected lag-24 ablation:

results/20260910T175101Z/

Forecast error analysis:

`results/forecast_analysis/`

Publication figures:

`results/forecast_analysis/figures/`

These corrected runs supersede earlier runs produced before the recursive forecasting alignment correction.