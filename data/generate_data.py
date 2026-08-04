import csv
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


def generate(path: str | Path = "data/api_logs.csv") -> Path:
    rng = random.Random(42)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) - timedelta(days=14)
    apis = [
        ("/payments", "POST", 430, 255, 58, 92),
        ("/orders", "GET", 520, 185, 42, 66),
        ("/inventory", "GET", 360, 220, 46, 74),
        ("/identity", "POST", 280, 145, 39, 54),
        ("/search", "GET", 650, 170, 44, 60),
    ]
    rows = []
    total_hours = 14 * 24
    for endpoint, method, base_req, base_latency, base_cpu, base_db in apis:
        for i in range(total_hours):
            ts = start + timedelta(hours=i)
            hour_wave = 1 + 0.28 * math.sin((ts.hour - 8) / 24 * 2 * math.pi)
            weekday = 1.12 if ts.weekday() < 5 else 0.82
            request_count = max(40, rng.gauss(base_req * hour_wave * weekday, base_req * 0.09))
            latency = rng.gauss(base_latency, base_latency * 0.08)
            cpu = rng.gauss(base_cpu, 5)
            db_latency = rng.gauss(base_db, 8)
            error_probability = 0.012

            if endpoint == "/payments" and i > total_hours - 30:
                surge = 1 + (i - (total_hours - 30)) / 30 * 0.72
                request_count *= surge
                db_latency *= 1.28 + (surge - 1) * 0.65
                latency *= 1.38 + (surge - 1) * 0.75
                cpu *= 1.18 + (surge - 1) * 0.45
                error_probability = 0.07 + (surge - 1) * 0.08
            if endpoint == "/inventory" and total_hours - 100 < i < total_hours - 82:
                db_latency *= 1.55
                latency *= 1.35
                error_probability = 0.045
            if endpoint == "/search" and total_hours - 65 < i < total_hours - 54:
                request_count *= 1.45
                latency *= 1.18

            status = 500 if rng.random() < error_probability else 404 if rng.random() < 0.025 else 200
            if status >= 500:
                latency *= rng.uniform(1.2, 1.7)
            rows.append(
                {
                    "timestamp": ts.isoformat(),
                    "api_id": endpoint.replace("/", ""),
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": status,
                    "response_time_ms": round(max(40, latency), 1),
                    "request_count": int(max(1, request_count)),
                    "cpu_usage": round(min(99, max(8, cpu)), 1),
                    "db_latency_ms": round(max(12, db_latency), 1),
                }
            )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "timestamp",
                "api_id",
                "endpoint",
                "method",
                "status_code",
                "response_time_ms",
                "request_count",
                "cpu_usage",
                "db_latency_ms",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    return path


if __name__ == "__main__":
    print(generate())
