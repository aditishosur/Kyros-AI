from datetime import datetime

from sqlalchemy.orm import Session

from backend import models
from backend.services.analytics import recent_metrics
from backend.services.ml import anomalies


def root_cause(db: Session, api_id: int) -> dict:
    api = db.query(models.API).filter(models.API.id == api_id).first()
    metrics = recent_metrics(db, api_id)
    anomaly_info = anomalies(db, api_id)
    if not api or not metrics:
        return {}

    traffic = round(metrics.get("traffic_delta", 0), 1)
    db_latency = round((metrics.get("db_latency", 0) / 90 - 1) * 100, 1)
    latency = round((metrics.get("avg_response_time", 0) / 300 - 1) * 100, 1)
    errors = round(metrics.get("error_rate", 0), 1)
    risk = metrics.get("risk_score", 0)

    if traffic > 25 and db_latency > 15:
        cause = "Database pressure caused by traffic surge"
        recommendation = "Increase service capacity and inspect database saturation before the next traffic peak."
    elif db_latency > 25:
        cause = "Database latency is the primary degradation driver"
        recommendation = "Investigate slow queries, connection pool saturation and database resource limits."
    elif errors > 5:
        cause = "Application error burst"
        recommendation = "Review recent deploys and error logs for elevated 5xx responses."
    else:
        cause = "Elevated performance risk"
        recommendation = "Continue monitoring and validate capacity headroom."

    severity = "Critical" if risk >= 70 else "High" if risk >= 55 else "Medium" if risk >= 35 else "Low"
    chain = [
        {"label": "Traffic spike", "value": f"{traffic:+.1f}%"},
        {"label": "Database latency", "value": f"{db_latency:+.1f}%"},
        {"label": "Response time", "value": f"{latency:+.1f}%"},
        {"label": "5xx errors", "value": f"{errors:.1f}%"},
        {"label": "API risk", "value": f"{risk:.0f}/100"},
    ]
    explanation = (
        f"Traffic moved {traffic:+.1f}% versus baseline, coinciding with database latency at "
        f"{metrics.get('db_latency', 0):.0f}ms and response time at {metrics.get('avg_response_time', 0):.0f}ms. "
        f"The correlation chain indicates {cause.lower()}."
    )
    incident = models.Incident(
        api_id=api_id,
        detected_at=datetime.utcnow(),
        severity=severity,
        root_cause=cause,
        explanation=explanation,
        recommendation=recommendation,
    )
    db.add(incident)
    db.commit()
    return {
        "api_id": api_id,
        "api_name": api.name,
        "detected_at": incident.detected_at.isoformat(),
        "severity": severity,
        "risk_score": risk,
        "probable_root_cause": cause,
        "confidence": "High" if anomaly_info["latest_is_anomaly"] or risk >= 65 else "Medium",
        "contributing_factors": metrics.get("contributors", {}),
        "supporting_metrics": metrics,
        "chain": chain,
        "explanation": explanation,
        "recommended_action": recommendation,
        "anomaly_detected": anomaly_info["latest_is_anomaly"],
    }

