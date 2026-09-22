# ⚡ PulseOps

## Predictive API Intelligence

> 🏆 **🥇 1st Place — College Hackathon 2026**

PulseOps is an API-operations intelligence platform that combines monitoring, workload forecasting, anomaly and early-warning analysis, transparent rule-based diagnosis, and scenario-based intervention estimation.

It is designed to help teams understand **what is happening, what may happen next, why it may be happening, and what could happen under a possible intervention.**

### 🔄 MONITOR → FORECAST → DETECT → DIAGNOSE → SIMULATE

---

## 🏆 Hackathon Achievement

PulseOps was developed as a college hackathon MVP and won **🥇 1st Place** among the participating teams.

The project combines Python, FastAPI, SQL-based telemetry storage, machine-learning forecasting, anomaly detection, rule-based diagnosis, scenario simulation, Streamlit, Docker, Kubernetes, and GitHub Actions.

The research contribution is an empirical evaluation of a lightweight integrated API-operations intelligence pipeline—not a claim of a novel machine-learning algorithm.

---

## 🔬 Research Story

```text
Operational Telemetry
        ↓
    FORECAST  → What workload is likely next?
        ↓
     DETECT   → Is degradation emerging, and how early?
        ↓
    DIAGNOSE  → What known cause is most consistent?
        ↓
    SIMULATE  → What could happen under an intervention?
        ↓
Comparison with reactive threshold monitoring
```

The system is evaluated using controlled synthetic telemetry and independent real/open telemetry where the dataset semantics support the relevant task.

---

## 📡 Monitor

The monitoring layer provides visibility into:

- Request volume
- Response latency
- Error rates
- Status codes
- Throughput
- API health indicators
- Recent incidents

The existing FastAPI and Streamlit application serves as the integration and demonstration layer. Research metrics are generated from offline experiment artifacts.

---

## 🔮 Forecast

The forecasting workstream evaluates whether workload forecasts can outperform simple temporal baselines on temporally held-out telemetry.

### Models

- Persistence / last-value baseline
- Seasonal-naive baseline using a 24-hour seasonal period
- Random Forest Regressor

### Evaluation

- Horizons: **1h, 6h, and 12h**
- Primary metrics: **MAE and RMSE**
- Secondary metrics: **sMAPE and R² where meaningful**
- Chronological train/validation/test splits
- Validation-only model selection
- Leakage-focused tests
- Offline, reproducible experiment runs

### Dataset B: GenTD26

The GenTD26 evaluation uses `lora_request_trace.csv` to construct a continuous hourly request-count series.

- Raw observations: 26,823
- Continuous hourly bins: 554
- Nonzero hourly bins: 370
- Zero-request hourly bins: 184
- Primary run: `20260921T155024Z`
- Ablation run: `20260921T155137Z`

The Dataset B analysis documents limitations involving anonymized or shifted timestamps, zero-request periods, limited temporal coverage, and independently tuned ablation configurations.

---

## 🧠 Detect

The anomaly and early-warning workstream evaluates whether degradation can be detected before reactive thresholds.

The planned comparison includes:

- A robust univariate threshold baseline
- Isolation Forest-based anomaly scoring

Evaluation focuses on event recall, PR-AUC where applicable, false-alert rate, warning lead time, and event-level precision/F1 where meaningful.

Synthetic telemetry and scenario labels are explicitly identified as such.

---

## 🔍 Diagnose

PulseOps uses transparent, rule-based, dependency-inspired reasoning to rank known possible causes.

This component is **not described as causal discovery or causal AI**.

Evaluation focuses on:

- Top-1 accuracy
- Top-2 accuracy
- Confusion matrices
- Representative explanation audits
- Performance across supported scenario types

---

## 🧪 Simulate

The simulation layer is a scenario/intervention simulator for exploring possible operational changes, including:

- Traffic increases or decreases
- Capacity changes
- Database-latency changes

Evaluation focuses on directional accuracy, delta MAE, and intervention-ranking agreement against independently generated or held-out outcomes.

The simulator is **not described as a causal counterfactual model**. Conclusions are limited to tested scenarios and parameter ranges.

---

## 🏗️ Architecture

```text
Synthetic / Real Operational Telemetry
                ↓
          Data Ingestion
                ↓
           SQL Storage
                ↓
        Feature Engineering
                ↓
       Offline Experiment Layer
                ↓
 ┌──────────┬──────────┬──────────┬──────────┐
 ↓          ↓          ↓          ↓
Forecast  Detect    Diagnose  Simulate
 └──────────┴──────────┴──────────┴──────────┘
                ↓
      Metrics, Predictions,
       Alerts, Explanations
                ↓
       FastAPI Integration API
                ↓
        Streamlit Demo Layer
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+ |
| API | FastAPI |
| Validation | Pydantic |
| Database ORM | SQLAlchemy |
| Database | SQLite |
| Machine Learning | scikit-learn |
| Data Processing | pandas, NumPy |
| Visualization | Plotly |
| Frontend | Streamlit |
| Containerization | Docker |
| Orchestration | Kubernetes |
| CI/CD | GitHub Actions |

---

## 📁 Research Artifacts

```text
results/
└── <run_id>/
    ├── metrics/
    ├── predictions/
    └── figures/
```

Research runs should record the run ID, Git commit hash, configuration, seed, input hash/version, UTC timestamp, and environment information where applicable.

Every paper result should be traceable to a stored result artifact.

---

## 🧪 Testing and Reproducibility

Run the test suite:

```bash
pytest
```

The forecasting workstream includes checks for chronological evaluation, leakage risks, forecasting aggregation, zero-filled hourly target construction, and prediction stability when future actual values are modified.

The forecasting implementation was verified with:

```text
24 passed, 4 warnings
```

A representative run should be reproducible by another teammate before its results are treated as final.

---

## 🔒 Research Boundaries

- Synthetic telemetry is clearly distinguished from real/open telemetry.
- Time-series evaluation uses temporal splits.
- Thresholds, model choices, and hyperparameters are selected using training/validation data only.
- Final test data is not used for tuning.
- Risk scoring is described as rule-based or heuristic.
- Diagnosis is described as rule-based, dependency-inspired reasoning.
- Simulation is described as scenario/intervention simulation.
- Negative or weak results are retained and used to narrow claims.
- The Streamlit application remains a demonstration layer; paper evidence comes from reproducible experiment artifacts.

---

## ⚡ PulseOps

**Monitor what is happening. Forecast what comes next. Detect emerging degradation. Diagnose supported causes. Simulate possible interventions.**