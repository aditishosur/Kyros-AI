# Cause Taxonomy Decision

Version: 1.0.0

The following labels are frozen for the first anomaly and RCA evaluation cycle:

| Scenario | Fault family | Primary cause |
| --- | --- | --- |
| normal | none | none |
| traffic_spike | demand | traffic_surge |
| latency_increase | service | service_delay |
| database_slowdown | database | database_slowdown |
| error_burst_5xx | application | application_error_burst |

Amulya must map rule-based RCA output to these exact `primary_cause` values before held-out evaluation. Resource saturation and combined degradation are deferred until the five essential scenarios pass their tests. Any later change requires a new taxonomy version and a new run; it must not alter an already-evaluated manifest.
