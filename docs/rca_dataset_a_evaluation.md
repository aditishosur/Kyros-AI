
# Kyros-AI: Dataset A Root-Cause Evaluation

## Objective

Evaluate the existing, deterministic Kyros-AI root-cause analysis (RCA)
rules against the frozen primary-cause labels in controlled Dataset A.

This experiment measures post-event, episode-level diagnostic agreement.
It does not evaluate causal discovery, early root-cause identification,
or performance on real production incidents.

## Dataset and evaluation split

Dataset A contains 100 independent synthetic telemetry episodes, each
168 hours long:

- Training: 10 normal episodes.
- Validation: 5 normal episodes and 40 fault episodes.
- Held-out test: 5 normal episodes and 40 fault episodes.

The four fault scenarios are traffic surge, service delay, database
slowdown, and application error burst. Each has 10 episodes in the
held-out test split.

The ground-truth cause is read from the frozen episode manifest's
`primary_cause` field.

## Prediction protocol

The experiment produces one RCA prediction per episode at zero-based
hour 131, the final hour of the configured event window. Normal episodes
are evaluated at the same hour.

Only observations at or before the prediction timestamp are used.
Telemetry from different episodes is never combined.

The input adapter uses the current observation and preceding six hourly
observations as the recent window. Traffic change compares mean request
count in this window against the mean of earlier observations within the
same episode.

Mean database latency is converted to percentage change relative to
90 ms. The adapter uses Dataset A's supplied error-rate percentages
because the dataset does not contain individual HTTP status-code logs.
This is a telemetry-level approximation of the application's
status-code-based error-rate calculation.

The original Kyros RCA decision rules, threshold values, and rule
priority remain unchanged.

## Ground-truth and prediction taxonomy

Dataset A has five ground-truth labels:

- `none`
- `traffic_surge`
- `service_delay`
- `database_slowdown`
- `application_error_burst`

The existing Kyros RCA produces four distinct outputs:

- `TRAFFIC_DB_PRESSURE`
- `DB_LATENCY`
- `APPLICATION_ERROR`
- `ELEVATED_RISK`

Only `DB_LATENCY` and `APPLICATION_ERROR` have unambiguous matches to
Dataset A's `database_slowdown` and `application_error_burst`,
respectively.

`TRAFFIC_DB_PRESSURE` is not equated with a pure traffic surge.
`ELEVATED_RISK` is a nonspecific fallback and is not equated with
`none`. Predictions without an unambiguous match are counted as
unsupported under the strict cross-taxonomy exact-match policy.

## Metrics

The experiment reports:

- Strict cross-taxonomy exact-match accuracy.
- Per-ground-truth-class exact-match recall.
- A cross-taxonomy confusion matrix retaining the original RCA outputs.
- The number of unsupported predictions.
- The fallback rate on normal-control episodes.

The normal-control fallback rate is not an independently established
false-positive rate because the existing RCA has no explicit normal or
abstention prediction.

Pooled outputs are saved for reproducibility, while held-out test
outputs are exported separately for reporting.

## Held-out test results

At prediction hour 131, the existing RCA produced 20 exact matches
among 45 held-out episodes: strict cross-taxonomy exact-match accuracy
of 44.44%.

All 10 database-slowdown episodes were assigned `DB_LATENCY`, and all
10 application-error-burst episodes were assigned `APPLICATION_ERROR`.

All 10 pure traffic-surge episodes, all 10 service-delay episodes, and
all 5 normal-control episodes received `ELEVATED_RISK`. No held-out
episode received `TRAFFIC_DB_PRESSURE`.

These observations describe the frozen synthetic Dataset A and this
specific post-event evaluation protocol. They do not establish
production diagnostic performance or superiority over another RCA
method.

## Reproduction

From the repository root, with the project environment activated:

```bash
python -m experiments.rca.run_dataset_a
python -m pytest tests/experiments/ -q
```

Held-out outputs are saved in `results/rca_dataset_a_v1/`:

- `test_episode_predictions.csv`
- `test_cross_taxonomy_confusion.csv`
- `test_per_class_metrics.csv`

The remaining CSVs in that directory contain pooled results across
training, validation, and test splits.

## Limitations

Dataset A is synthetic and contains no training fault episodes.
Consequently, a fault-cause frequency baseline cannot be estimated
from its training split alone.

The evaluation uses a fixed post-event prediction time rather than
measuring detection-to-diagnosis latency. It also uses a telemetry-level
error-rate adapter instead of reconstructing individual HTTP requests.

The current RCA has no dedicated rule for independent service delay,
no explicit normal output, and no pure traffic-surge rule without
simultaneous database-latency elevation. The experiment preserves these
limitations rather than modifying the rules after observing test results.
