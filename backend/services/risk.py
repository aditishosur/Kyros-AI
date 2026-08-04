def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def health_status(risk: float) -> str:
    if risk >= 70:
        return "Critical"
    if risk >= 40:
        return "Degraded"
    return "Healthy"


def calculate_risk(metrics: dict) -> dict:
    error_rate = metrics.get("error_rate", 0)
    avg_latency = metrics.get("avg_latency", 0)
    p95_latency = metrics.get("p95_latency", avg_latency)
    traffic_delta = metrics.get("traffic_delta", 0)
    failure_trend = metrics.get("failure_trend", 0)
    cpu = metrics.get("cpu_usage", 0)
    db_latency = metrics.get("db_latency", 0)

    contributors = {
        "Error rate": clamp(error_rate * 4.2, 0, 28),
        "Response-time anomaly": clamp((p95_latency - 300) / 20, 0, 22),
        "Traffic spike": clamp(traffic_delta * 0.45, 0, 18),
        "Recent failure trend": clamp(failure_trend * 2.8, 0, 14),
        "CPU usage": clamp((cpu - 55) * 0.35, 0, 10),
        "DB latency": clamp((db_latency - 90) * 0.16, 0, 18),
    }
    score = clamp(sum(contributors.values()))
    return {
        "risk_score": round(score, 1),
        "status": health_status(score),
        "contributors": {k: round(v, 1) for k, v in contributors.items()},
    }

