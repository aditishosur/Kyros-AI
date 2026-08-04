from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend import models
from backend.services.risk import calculate_risk


def logs_frame(db: Session, api_id: int | None = None) -> pd.DataFrame:
    query = db.query(models.APILog)
    if api_id:
        query = query.filter(models.APILog.api_id == api_id)
    rows = query.order_by(models.APILog.timestamp).all()
    data = [
        {
            "id": r.id,
            "api_id": r.api_id,
            "timestamp": r.timestamp,
            "status_code": r.status_code,
            "response_time_ms": r.response_time_ms,
            "request_count": r.request_count,
            "cpu_usage": r.cpu_usage,
            "db_latency_ms": r.db_latency_ms,
        }
        for r in rows
    ]
    return pd.DataFrame(data)


def summarize_frame(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "total_requests": 0,
            "avg_response_time": 0,
            "p95_response_time": 0,
            "error_rate": 0,
            "status_distribution": {},
        }
    total_requests = int(df["request_count"].sum())
    errors = df[df["status_code"] >= 500]["request_count"].sum()
    status_distribution = {
        "2xx": int(df[df["status_code"].between(200, 299)]["request_count"].sum()),
        "4xx": int(df[df["status_code"].between(400, 499)]["request_count"].sum()),
        "5xx": int(errors),
    }
    return {
        "total_requests": total_requests,
        "avg_response_time": round(float(df["response_time_ms"].mean()), 1),
        "p95_response_time": round(float(np.percentile(df["response_time_ms"], 95)), 1),
        "error_rate": round(float(errors / max(total_requests, 1) * 100), 2),
        "status_distribution": status_distribution,
    }


def recent_metrics(db: Session, api_id: int) -> dict:
    df = logs_frame(db, api_id)
    if df.empty:
        return {}
    latest_window = df[df["timestamp"] >= df["timestamp"].max() - timedelta(hours=6)]
    baseline = df[df["timestamp"] < df["timestamp"].max() - timedelta(hours=6)]
    if baseline.empty:
        baseline = df
    summary = summarize_frame(latest_window)
    baseline_requests = max(float(baseline["request_count"].mean()), 1)
    recent_requests = float(latest_window["request_count"].mean())
    recent_errors = latest_window[latest_window["status_code"] >= 500]["request_count"].sum()
    previous_errors = baseline[baseline["status_code"] >= 500]["request_count"].sum()
    failure_trend = (recent_errors / max(latest_window["request_count"].sum(), 1) * 100) - (
        previous_errors / max(baseline["request_count"].sum(), 1) * 100
    )
    metrics = {
        **summary,
        "avg_latency": summary["avg_response_time"],
        "p95_latency": summary["p95_response_time"],
        "traffic_delta": (recent_requests - baseline_requests) / baseline_requests * 100,
        "failure_trend": max(failure_trend, 0),
        "cpu_usage": float(latest_window["cpu_usage"].mean()),
        "db_latency": float(latest_window["db_latency_ms"].mean()),
        "request_rate": recent_requests,
        "latest_timestamp": latest_window["timestamp"].max().isoformat(),
    }
    metrics.update(calculate_risk(metrics))
    return metrics


def overview(db: Session) -> dict:
    apis = db.query(models.API).order_by(models.API.name).all()
    df = logs_frame(db)
    summary = summarize_frame(df)
    api_rows = []
    for api in apis:
        metrics = recent_metrics(db, api.id)
        risk = metrics.get("risk_score", 0)
        api_rows.append(
            {
                "id": api.id,
                "name": api.name,
                "endpoint": api.endpoint,
                "method": api.method,
                "owner": api.owner,
                "status": metrics.get("status", api.status),
                "risk_score": risk,
                "traffic": round(metrics.get("request_rate", 0), 1),
                "traffic_delta": round(metrics.get("traffic_delta", 0), 1),
                "latency": metrics.get("avg_response_time", 0),
                "p95_latency": metrics.get("p95_response_time", 0),
                "error_rate": metrics.get("error_rate", 0),
                "anomaly": risk >= 65,
                "db_latency": round(metrics.get("db_latency", 0), 1),
                "cpu_usage": round(metrics.get("cpu_usage", 0), 1),
            }
        )
    summary.update(
        {
            "apis_monitored": len(apis),
            "healthy_apis": sum(1 for row in api_rows if row["status"] == "Healthy"),
            "at_risk_apis": sum(1 for row in api_rows if row["status"] != "Healthy"),
            "incidents": db.query(models.Incident).count(),
            "last_updated": datetime.utcnow().isoformat(),
            "apis": api_rows,
        }
    )
    return summary


def api_analytics(db: Session, api_id: int) -> dict:
    api = db.query(models.API).filter(models.API.id == api_id).first()
    if not api:
        return {}
    df = logs_frame(db, api_id)
    metrics = recent_metrics(db, api_id)
    timeseries = []
    if not df.empty:
        hourly = (
            df.assign(timestamp=pd.to_datetime(df["timestamp"]))
            .set_index("timestamp")
            .resample("h")
            .agg(
                request_count=("request_count", "sum"),
                response_time_ms=("response_time_ms", "mean"),
                error_rate=("status_code", lambda s: float((s >= 500).mean() * 100)),
                cpu_usage=("cpu_usage", "mean"),
                db_latency_ms=("db_latency_ms", "mean"),
            )
            .reset_index()
        )
        timeseries = hourly.to_dict(orient="records")
    return {
        "api": {
            "id": api.id,
            "name": api.name,
            "endpoint": api.endpoint,
            "method": api.method,
            "owner": api.owner,
            "description": api.description,
        },
        "metrics": metrics,
        "timeseries": timeseries,
    }

