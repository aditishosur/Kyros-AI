# Forecasting Results

## Aggregate MAE

| Horizon | Persistence | Random Forest | Seasonal Naive |
|---:|---:|---:|---:|
| 1h | 55.25 | 58.10 | 115.10 |
| 6h | 118.63 | 76.54 | 118.28 |
| 12h | 170.92 | 84.72 | 113.32 |

## Main Finding

Random Forest does not outperform Persistence at the 1-hour horizon.

At 6-hour and 12-hour horizons, Random Forest achieves substantially lower MAE than Persistence.

Random Forest also outperforms Seasonal Naive at all tested horizons in aggregate.

## Ablation

Removing `lag_24` changes mean MAE by:

| Horizon | MAE change |
|---:|---:|
| 1h | -3.92% |
| 6h | -6.56% |
| 12h | -10.19% |

Removing `lag_24` improves performance in 13 of 15 endpoint-horizon combinations.

## Failure Case

The `/payments` endpoint is the principal Random Forest failure case.

Random Forest has higher MAE than Persistence for `/payments` at all three evaluated horizons.