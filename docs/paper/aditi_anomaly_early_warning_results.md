# Anomaly and Early Warning Results

## Held-Out Controlled Dataset A

The locked detectors were evaluated on held-out controlled episodes with previously unseen event seeds and higher intensity levels than validation. The robust latency baseline achieved event recall of 0.800, early-warning recall of 0.200, PR-AUC of 0.604, and a false-alert rate of 0.915 alert intervals per 100 normal hours. Among the eight events that received an early warning, the median lead time was 9.5 hours with an IQR of 7.0 hours.

Isolation Forest achieved event recall of 1.000 and PR-AUC of 0.680. Its early-warning recall was 0.125: five events received a valid warning-window alert, with a median lead time of 11.0 hours and an IQR of 10.0 hours. Its false-alert rate was 1.144 alert intervals per 100 normal hours. Thus, Isolation Forest detected every held-out event by event end and produced a higher continuous-score discrimination result than the robust baseline, but it did not provide an early warning for most events and incurred a modestly higher false-alert rate.

The reactive latency-or-error threshold achieved event recall of 0.725 and early-warning recall of 0.000, with zero false-alert intervals. It therefore provided no pre-onset warning under the frozen convention. This comparison supports the narrow conclusion that the evaluated learned and robust detectors can sometimes provide earlier signals than the reactive comparator on controlled faults; it does not establish universal early-warning superiority.

| Detector | Event recall | Early-warning recall | PR-AUC | False-alert rate per 100 normal hours | Median lead time, hours | Lead-time IQR, hours |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Robust latency baseline | 0.800 | 0.200 | 0.604 | 0.915 | 9.5 | 7.0 |
| Isolation Forest | 1.000 | 0.125 | 0.680 | 1.144 | 11.0 | 10.0 |
| Reactive threshold | 0.725 | 0.000 | 0.671 | 0.000 | Not applicable | Not applicable |

The reactive PR-AUC is reported only as a score-derived secondary value in the saved metrics. It must not be interpreted as learned anomaly discrimination. The primary comparison is event detection, early-warning recall, lead time, and false-alert behavior.

## External NAB Result

The external NAB evaluation was intentionally narrower. On two eligible labelled test events, the univariate Isolation Forest achieved event recall of 0.500, event precision of 1.000, event F1 of 0.667, PR-AUC of 0.323, ROC-AUC of 0.493, and zero false-alert intervals. These results are not evidence for multivariate API degradation detection or warning lead time. They provide only a limited external check of score-based anomaly-window discrimination on a real labelled series with different signal semantics.

## Limitations

Dataset A is synthetic and should be described as controlled scenario evidence, not production performance. The test episodes are temporally separated by generated episode order and use held-out seeds and intensity levels, but their mechanisms remain those of the generator. Dataset B has real labelled anomaly windows but lacks the API telemetry meanings and distinct warning labels required for the full Dataset A analysis. The existing RCA output taxonomy also does not map one-to-one to the frozen Dataset A primary-cause labels; this must remain a documented integration limitation rather than being presented as complete cause-label agreement.

## Reproducibility Artifacts

The controlled results are stored under `results/anomaly_final_001/`, including `metrics/anomaly_metrics.csv`, the event and false-alert tables, continuous hourly scores, the scenario manifest, locked detector configuration, and `figures/alert_timeline.html`. The NAB result is stored under `results/dataset_b_nab_001/`, including the adapted series, scores, event and false-alert tables, metrics, adapter report, and run metadata.
