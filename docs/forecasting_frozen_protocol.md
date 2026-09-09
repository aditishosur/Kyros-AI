# Kyros-AI Forecasting — Frozen Experimental Protocol

## Target

Hourly `request_count` per endpoint.

## Dataset

Dataset A: `data/api_logs.csv`

The dataset contains 5 API endpoints with hourly observations.

## Temporal Split

Chronological 60/20/20 split:

- Training: 202 timestamps
- Validation: 67 timestamps
- Test: 67 timestamps

No shuffling is used.

The test period remains untouched during model selection.

## Forecast Horizons

- 1 hour
- 6 hours
- 12 hours

## Models

### Persistence

Predicts using the most recently observed workload value.

### Seasonal Naive

Uses a 24-hour seasonal lag.

### Random Forest

Random Forest Regressor with:

- `n_estimators = 100`
- `min_samples_leaf = 1`
- `max_depth = None`
- `random_state = 42`

## Random Forest Features

- `hour`
- `day_of_week`
- `lag_1`
- `lag_3`
- `lag_6`
- `lag_24`
- `rolling_mean_6`
- `rolling_mean_24`

Rolling features use shifted observations so that only information available before the forecast origin is used.

## Model Selection

Random Forest configuration was selected using validation performance.

The test set was not used for configuration selection.

## Evaluation Metrics

Primary:

- MAE
- RMSE

Secondary:

- sMAPE

## Forecast Evaluation

Forecasts are evaluated using rolling forecast origins.

Recursive Random Forest forecasting uses previously generated predictions for future recursive steps rather than future observed values.

## Leakage Controls

- Chronological splitting
- No shuffling
- Lag features use historical observations
- Rolling features use shifted observations
- Test observations are not used for model selection
- Random Forest configuration is frozen before final test evaluation

## Primary Experiment Run

`20260909T132210Z`

## Ablation Run

`20260909T134219Z`

The feature ablation compares the full feature set against a configuration without `lag_24`.

The ablation is reported separately from the primary frozen model.

## Frozen Scientific Conclusions

The Random Forest does not outperform Persistence at the 1-hour horizon in aggregate.

At 6-hour and 12-hour horizons, Random Forest substantially outperforms Persistence.

Random Forest outperforms Seasonal Naive across the tested endpoint-horizon combinations.

The `/payments` endpoint represents an important failure case where Random Forest underperforms Persistence.

Removing `lag_24` improves MAE across most endpoint-horizon combinations, but this does not establish that the feature is universally harmful.

## Status

The core Dataset A forecasting experiment is frozen.

No further feature or hyperparameter search should be performed unless a methodological error is discovered.