# Dataset B Shortlist

The shortlist distinguishes external validation from a claim that every source is equivalent to API telemetry.

## Selected limited validation source: Numenta Anomaly Benchmark

NAB contains labelled streaming time series, including real-world data, and its public repository states that the corpus contains labelled anomalous periods. Its repository licence is MIT. It is selected only for an external anomaly-detection sensitivity check.

NAB does not provide the complete Kyros API telemetry feature set. A NAB value must not be renamed as API latency, request count, or error rate. The adapter must preserve the source value and document its original metric. The dataset can support labelled anomaly-window PR-AUC, ROC-AUC, event recall, and false-alert comparisons when labels are converted transparently into events. It cannot validate Kyros multivariate Isolation Forest fairly and cannot support the frozen early-warning lead-time convention because it does not provide a separately labelled pre-onset warning period.

Sources: <https://github.com/numenta/NAB> and <https://github.com/numenta/NAB/blob/master/LICENSE.txt>.

## Rejected for early-warning metrics: Google cluster-usage traces v3

The Google trace supplies resource-usage telemetry but no supplied anomaly or incident labels. It cannot support event recall, PR-AUC, or warning lead time for this research question without invented ground truth.

## Shortlisted but blocked pending licence verification: AIOps 2018 KPI anomaly data

This source appears relevant for labelled KPI anomaly evaluation. It remains unselected until its official licence and source-column semantics are verified and recorded.
