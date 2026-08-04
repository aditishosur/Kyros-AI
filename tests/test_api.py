from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_crud():
    payload = {
        "name": "Billing API",
        "endpoint": "/billing-test",
        "method": "GET",
        "owner": "Finance Platform",
        "description": "CRUD test API",
        "status": "Healthy",
    }
    created = client.post("/apis", json=payload)
    assert created.status_code == 201
    api_id = created.json()["id"]
    fetched = client.get(f"/apis/{api_id}")
    assert fetched.status_code == 200
    updated = client.put(f"/apis/{api_id}", json={"owner": "Revenue Engineering"})
    assert updated.status_code == 200
    assert updated.json()["owner"] == "Revenue Engineering"
    deleted = client.delete(f"/apis/{api_id}")
    assert deleted.status_code == 204


def test_overview_and_api_analytics():
    overview = client.get("/analytics/overview")
    assert overview.status_code == 200
    body = overview.json()
    assert body["total_requests"] > 0
    assert body["apis_monitored"] >= 5
    payments = next(api for api in body["apis"] if api["endpoint"] == "/payments")
    detail = client.get(f"/analytics/apis/{payments['id']}")
    assert detail.status_code == 200
    assert detail.json()["metrics"]["risk_score"] >= 0


def test_risk_root_cause_forecast_and_simulation():
    overview = client.get("/analytics/overview").json()
    payments = next(api for api in overview["apis"] if api["endpoint"] == "/payments")
    api_id = payments["id"]

    risk = client.get(f"/analytics/apis/{api_id}/risk")
    assert risk.status_code == 200
    assert "contributors" in risk.json()

    rca = client.get(f"/analytics/apis/{api_id}/root-cause")
    assert rca.status_code == 200
    assert rca.json()["probable_root_cause"]
    assert len(rca.json()["chain"]) == 5

    forecast = client.get(f"/predictions/{api_id}")
    assert forecast.status_code == 200
    assert len(forecast.json()["forecast"]) > 0

    sim = client.post(
        "/simulation/run",
        json={"api_id": api_id, "traffic_change": 50, "capacity_change": -20, "db_latency_change": 10},
    )
    assert sim.status_code == 200
    assert sim.json()["simulated"]["risk"] >= sim.json()["current"]["risk"]

