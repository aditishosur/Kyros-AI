from sqlalchemy.orm import Session

from backend import models
from backend.services.analytics import recent_metrics
from backend.services.risk import calculate_risk, health_status


def run_simulation(db: Session, api_id: int, traffic_change: float, capacity_change: float, db_latency_change: float) -> dict:
    current = recent_metrics(db, api_id)
    if not current:
        return {}
    traffic_factor = 1 + traffic_change / 100
    capacity_factor = max(0.25, 1 + capacity_change / 100)
    db_factor = 1 + db_latency_change / 100
    pressure = max(traffic_factor / capacity_factor, 0.1)

    simulated_requests = current["request_rate"] * traffic_factor
    simulated_db = current["db_latency"] * db_factor * (1 + max(pressure - 1, 0) * 0.35)
    simulated_latency = current["avg_response_time"] * (1 + max(pressure - 1, 0) * 0.85) + (simulated_db - current["db_latency"]) * 0.65
    simulated_error_rate = max(0, current["error_rate"] + max(pressure - 1, 0) * 8 + max(db_factor - 1, 0) * 3)
    metrics = {
        "error_rate": simulated_error_rate,
        "avg_latency": simulated_latency,
        "p95_latency": simulated_latency * 1.35,
        "traffic_delta": traffic_change,
        "failure_trend": simulated_error_rate - current["error_rate"],
        "cpu_usage": min(99, current["cpu_usage"] * pressure),
        "db_latency": simulated_db,
    }
    risk = calculate_risk(metrics)["risk_score"]
    status = health_status(risk)
    if risk >= 70 and capacity_change < traffic_change:
        recommendation = "High risk: increase capacity before applying this traffic scenario and reduce database pressure."
    elif db_latency_change > 20:
        recommendation = "Database latency is the limiting factor; tune queries or add database capacity before launch."
    elif risk >= 40:
        recommendation = "Proceed cautiously with active monitoring and a rollback plan."
    else:
        recommendation = "Scenario remains within acceptable operating range."

    record = models.Simulation(
        api_id=api_id,
        traffic_change=traffic_change,
        capacity_change=capacity_change,
        db_latency_change=db_latency_change,
        predicted_latency=simulated_latency,
        predicted_error_rate=simulated_error_rate,
        predicted_risk=risk,
        recommendation=recommendation,
    )
    db.add(record)
    db.commit()
    return {
        "api_id": api_id,
        "current": {
            "request_rate": round(current["request_rate"], 1),
            "latency": current["avg_response_time"],
            "error_rate": current["error_rate"],
            "risk": current["risk_score"],
            "health": current["status"],
        },
        "simulated": {
            "request_rate": round(simulated_requests, 1),
            "latency": round(simulated_latency, 1),
            "error_rate": round(simulated_error_rate, 2),
            "risk": round(risk, 1),
            "health": status,
        },
        "impact": {
            "latency_change_pct": round((simulated_latency / max(current["avg_response_time"], 1) - 1) * 100, 1),
            "error_rate_delta": round(simulated_error_rate - current["error_rate"], 2),
            "risk_delta": round(risk - current["risk_score"], 1),
        },
        "recommendation": recommendation,
        "label": "SIMULATED/PREDICTED",
    }

