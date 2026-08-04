from datetime import timedelta

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sqlalchemy.orm import Session

from backend import models
from backend.services.analytics import logs_frame, recent_metrics
from backend.services.risk import calculate_risk


def _hourly(df: pd.DataFrame) -> pd.DataFrame:
    return (
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
        .ffill()
        .reset_index()
    )


def _features(hourly: pd.DataFrame) -> pd.DataFrame:
    data = hourly.copy()
    data["hour"] = data["timestamp"].dt.hour
    data["day_of_week"] = data["timestamp"].dt.dayofweek
    for lag in [1, 3, 6, 24]:
        data[f"lag_{lag}"] = data["request_count"].shift(lag)
    data["rolling_mean_6"] = data["request_count"].rolling(6).mean()
    data["rolling_mean_24"] = data["request_count"].rolling(24).mean()
    feature_cols = ["hour", "day_of_week", "lag_1", "lag_3", "lag_6", "lag_24", "rolling_mean_6", "rolling_mean_24"]
    return data.dropna(subset=feature_cols).reset_index(drop=True)


def forecast(db: Session, api_id: int, horizon: int = 12) -> dict:
    df = logs_frame(db, api_id)
    if df.empty or len(df) < 48:
        return {"api_id": api_id, "historical": [], "forecast": [], "summary": {}}
    hourly = _hourly(df)
    feature_cols = ["hour", "day_of_week", "lag_1", "lag_3", "lag_6", "lag_24", "rolling_mean_6", "rolling_mean_24"]
    train = _features(hourly).dropna(subset=["request_count"])
    model = RandomForestRegressor(n_estimators=140, random_state=42, min_samples_leaf=2)
    model.fit(train[feature_cols], train["request_count"])

    working = hourly[["timestamp", "request_count", "response_time_ms", "error_rate", "cpu_usage", "db_latency_ms"]].copy()
    forecast_rows = []
    for step in range(horizon):
        next_ts = working["timestamp"].max() + timedelta(hours=1)
        temp = pd.concat(
            [
                working,
                pd.DataFrame(
                    [{
                        "timestamp": next_ts,
                        "request_count": np.nan,
                        "response_time_ms": working["response_time_ms"].tail(6).mean(),
                        "error_rate": working["error_rate"].tail(6).mean(),
                        "cpu_usage": working["cpu_usage"].tail(6).mean(),
                        "db_latency_ms": working["db_latency_ms"].tail(6).mean(),
                    }]
                ),
            ],
            ignore_index=True,
        )
        feats = _features(temp).tail(1)
        predicted = max(float(model.predict(feats[feature_cols])[0]), 0)
        working.loc[len(working)] = [next_ts, predicted, working["response_time_ms"].tail(6).mean(), working["error_rate"].tail(6).mean(), working["cpu_usage"].tail(6).mean(), working["db_latency_ms"].tail(6).mean()]
        latency = float(working["response_time_ms"].tail(12).mean() * (1 + max(predicted / max(hourly["request_count"].tail(24).mean(), 1) - 1, 0) * 0.25))
        error_rate = float(working["error_rate"].tail(12).mean() + max(predicted / max(hourly["request_count"].tail(24).mean(), 1) - 1, 0) * 2.5)
        risk = calculate_risk(
            {
                "error_rate": error_rate,
                "avg_latency": latency,
                "p95_latency": latency * 1.35,
                "traffic_delta": (predicted / max(hourly["request_count"].tail(24).mean(), 1) - 1) * 100,
                "failure_trend": error_rate,
                "cpu_usage": float(working["cpu_usage"].tail(6).mean()),
                "db_latency": float(working["db_latency_ms"].tail(6).mean()),
            }
        )["risk_score"]
        forecast_rows.append(
            {
                "timestamp": next_ts.isoformat(),
                "predicted_request_count": round(predicted, 1),
                "predicted_latency": round(latency, 1),
                "predicted_error_rate": round(error_rate, 2),
                "predicted_risk": round(risk, 1),
            }
        )
    peak = max(forecast_rows, key=lambda row: row["predicted_request_count"])
    current = recent_metrics(db, api_id)
    summary = {
        "predicted_peak_traffic": peak["predicted_request_count"],
        "peak_time": peak["timestamp"],
        "expected_growth": round((peak["predicted_request_count"] / max(float(hourly["request_count"].tail(6).mean()), 1) - 1) * 100, 1),
        "current_risk": current.get("risk_score", 0),
        "predicted_risk": peak["predicted_risk"],
        "capacity": round(float(hourly["request_count"].quantile(0.9) * 1.12), 1),
    }
    for row in forecast_rows:
        db.add(
            models.Prediction(
                api_id=api_id,
                timestamp=pd.to_datetime(row["timestamp"]).to_pydatetime(),
                predicted_request_count=row["predicted_request_count"],
                predicted_latency=row["predicted_latency"],
                predicted_error_rate=row["predicted_error_rate"],
                predicted_risk=row["predicted_risk"],
            )
        )
    db.commit()
    return {
        "api_id": api_id,
        "historical": hourly.tail(48).assign(timestamp=lambda x: x["timestamp"].dt.isoformat()).to_dict(orient="records"),
        "forecast": forecast_rows,
        "summary": summary,
    }


def anomalies(db: Session, api_id: int) -> dict:
    df = logs_frame(db, api_id)
    if df.empty:
        return {"anomalies": [], "latest_is_anomaly": False}
    hourly = _hourly(df)
    features = hourly[["request_count", "response_time_ms", "error_rate", "cpu_usage", "db_latency_ms"]].fillna(0)
    model = IsolationForest(contamination=0.08, random_state=42)
    hourly["anomaly"] = model.fit_predict(features) == -1
    return {
        "latest_is_anomaly": bool(hourly["anomaly"].iloc[-1]),
        "anomalies": hourly[hourly["anomaly"]].assign(timestamp=lambda x: x["timestamp"].dt.isoformat()).tail(20).to_dict(orient="records"),
    }
