# 🔌PulseOps

> **Predictive API Intelligence for Enterprise API Operations**

Kyros is an AI-powered API Intelligence Platform that goes beyond traditional monitoring by helping engineering teams **predict**, **understand**, **simulate**, and **optimize** API performance before issues impact production.

### Core Intelligence Pipeline

```text
MONITOR → PREDICT → EXPLAIN → SIMULATE → RECOMMEND
```

Unlike conventional monitoring tools that only report failures, **Kyros** identifies *why* an issue occurred and enables engineers to simulate future outcomes before implementing infrastructure or configuration changes.

---

# ✨ Features

- ⚡ FastAPI REST Backend with Swagger/OpenAPI
- 🗄️ SQLite Database with SQLAlchemy ORM
- 📊 Deterministic Synthetic API Telemetry Generator
- 📈 API Health & Risk Scoring
- 🤖 Random Forest Traffic Forecasting
- 🚨 Isolation Forest Anomaly Detection
- 🧠 Explainable Root Cause Analysis Engine
- 🔮 What-If Impact Simulation
- 📉 Interactive Streamlit + Plotly Dashboard
- 🐳 Docker & Docker Compose Support
- ☸️ Kubernetes Deployment Manifests
- 🔄 GitHub Actions CI Pipeline
- ✅ Pytest Test Coverage

---

# 🏗️ Architecture

```text
                  Synthetic API Telemetry
                           │
                           ▼
              SQLite Database (SQLAlchemy)
                           │
                           ▼
                  FastAPI REST Backend
                           │
      ┌────────────────────┼────────────────────┐
      │                    │                    │
      ▼                    ▼                    ▼
Risk Scoring      Traffic Forecasting    Anomaly Detection
      │                    │                    │
      └──────────────┬─────┴──────────────┬─────┘
                     ▼
          Root Cause Analysis Engine
                     │
                     ▼
          What-If Simulation Engine
                     │
                     ▼
        Streamlit Enterprise Dashboard
```

---

# 📂 Project Structure

```text
backend/
│── main.py
│── database.py
│── models.py
│── schemas.py
│── bootstrap.py
└── services/

frontend/
│── app.py
│── client.py
└── components/

data/
│── generate_data.py
└── api_logs.csv

tests/
k8s/

.github/
└── workflows/
    └── ci.yml

Dockerfile
docker-compose.yml
requirements.txt
README.md
```

---

# 🚀 Local Setup

### 1. Create a Virtual Environment

```bash
python -m venv .venv
```

### 2. Activate Environment

**Windows**

```bash
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Generate Demo Data

```bash
python data/generate_data.py
```

---

## Start Backend

```bash
uvicorn backend.main:app --reload --port 8000
```

## Start Frontend

```bash
streamlit run frontend/app.py
```

---

## Access the Application

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:8501 |
| Swagger Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

> The SQLite database initializes automatically on first startup.

---

# 🔗 API Endpoints

## Health

```
GET /health
```

## API Registry

```
GET    /apis
GET    /apis/{id}
POST   /apis
PUT    /apis/{id}
DELETE /apis/{id}
```

## Analytics

```
GET /analytics/overview
GET /analytics/apis/{id}
GET /analytics/apis/{id}/risk
GET /analytics/apis/{id}/root-cause
GET /analytics/apis/{id}/anomalies
```

## Machine Learning

```
GET /predictions/{id}
```

## Simulation

```
POST /simulation/run
```

---

# 🗄️ Database Schema

The platform consists of five primary tables:

| Table | Purpose |
|--------|----------|
| **apis** | API catalog and ownership |
| **api_logs** | Telemetry including latency, traffic, CPU usage, and status |
| **predictions** | Forecast outputs |
| **incidents** | Root cause incidents |
| **simulations** | What-if simulation history |

All operational records maintain foreign-key relationships with the **apis** table.

---

# 🤖 Machine Learning Pipeline

### Traffic Forecasting

Model:

```
RandomForestRegressor(random_state=42)
```

Features include:

- Hour
- Day of Week
- Lag 1 Hour
- Lag 3 Hours
- Lag 6 Hours
- Lag 24 Hours
- Rolling Mean (6h)
- Rolling Mean (24h)

---

### Anomaly Detection

Model:

```
IsolationForest(random_state=42)
```

Input Metrics

- Traffic
- Response Time
- Error Rate
- CPU Usage
- Database Latency

---

### Explainable Root Cause Analysis

The RCA engine is deterministic and correlates:

```
Traffic
↓
Database Latency
↓
Response Time
↓
5xx Errors
↓
API Risk
```

It produces both a causal explanation and recommended remediation.

---

# ⭐ Core Capabilities

## 🛡️ API Health & Risk Intelligence

Calculates a comprehensive **0–100 risk score** using:

- Error Rate
- Latency
- CPU Utilization
- Database Latency
- Traffic Spikes
- Failure Trends

---

## 📈 Predictive Traffic Forecasting

Forecasts future request volume and estimates:

- Capacity Gap
- Peak Traffic
- Infrastructure Risk

---

## 🔍 Explainable Root Cause Analysis

Automatically generates human-readable causal chains, for example:

```text
Traffic Spike
      ↓
Database Latency
      ↓
Response Time
      ↓
5xx Errors
      ↓
High API Risk
```

---

## 🔮 What-If Impact Simulation

Engineers can simulate changes to:

- Traffic Load
- Infrastructure Capacity
- Database Latency

Kyros predicts the resulting latency, error rate, health score, and operational risk before deployment.

---

# 🖥️ Dashboard Pages

- 🏠 Landing
- 📊 Operations Center
- 🧠 API Intelligence
- 📈 Traffic Forecast
- 🚨 Incidents & Root Cause
- 🔮 What-If Simulator
- 📚 API Registry

---

# 🎬 Demo Flow

1. Launch the Landing Page.
2. Open the Operations Center.
3. Inspect the degraded **Payments API**.
4. View API Intelligence.
5. Analyze the Health & Risk Score.
6. Review Traffic Forecast.
7. Explore Capacity Outlook.
8. Open Incident Intelligence.
9. Review Root Cause Analysis.
10. Navigate to the What-If Simulator.
11. Apply:
   - Traffic → **+50%**
   - Capacity → **−20%**
   - Database Latency → **+10%**
12. Run the simulation and review the predicted operational impact.

---

# 🧪 Testing

Run the complete test suite:

```bash
pytest -q
```

Coverage includes:

- Health Endpoint
- CRUD Operations
- Analytics APIs
- Risk Scoring
- Root Cause Engine
- Forecasting
- Simulation Engine

---

# 🐳 Docker

Build the image:

```bash
docker build -t kyros:latest .
```

Run the container:

```bash
docker run --rm -p 8000:8000 -p 8501:8501 kyros:latest
```

Using Docker Compose:

```bash
docker compose up --build
```

---

# ☸️ Kubernetes

Deploy to Docker Desktop or Minikube:

```bash
docker build -t kyros:latest .
kubectl apply -f k8s/
kubectl get pods

kubectl port-forward svc/kyros-frontend 8501:8501
kubectl port-forward svc/kyros-api 8000:8000
```

Dashboard:

```
http://localhost:8501
```

---

# 🔄 CI/CD

The GitHub Actions workflow automatically:

- Installs dependencies
- Generates demo telemetry
- Executes the test suite
- Imports backend and frontend modules
- Builds the Docker image

---

# ⚠️ Known Limitations

- SQLite is used for rapid prototyping and hackathon deployment.
- Production deployments should migrate to PostgreSQL with managed migrations.
- Synthetic telemetry is deterministic and designed for demonstrations.
- Root Cause Analysis is rule-based and fully explainable rather than LLM-generated.
- Forecast confidence is represented through capacity gap and forecast regions instead of calibrated statistical confidence intervals.
