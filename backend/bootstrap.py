from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from backend import models
from backend.database import Base, DATA_DIR, engine


def init_db(db: Session) -> None:
    Base.metadata.create_all(bind=engine)
    if db.query(models.API).count() > 0:
        return
    csv_path = DATA_DIR / "api_logs.csv"
    if not csv_path.exists():
        from data.generate_data import generate

        generate(csv_path)

    apis = [
        models.API(name="Payments API", endpoint="/payments", method="POST", owner="Revenue Platform", description="Payment authorization and capture workflow"),
        models.API(name="Orders API", endpoint="/orders", method="GET", owner="Commerce Core", description="Order history and order status retrieval"),
        models.API(name="Inventory API", endpoint="/inventory", method="GET", owner="Supply Systems", description="Inventory availability and reservation checks"),
        models.API(name="Identity API", endpoint="/identity", method="POST", owner="IAM", description="Authentication and token exchange"),
        models.API(name="Search API", endpoint="/search", method="GET", owner="Experience Platform", description="Product and content search"),
    ]
    db.add_all(apis)
    db.commit()
    by_endpoint = {api.endpoint: api.id for api in db.query(models.API).all()}
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    rows = []
    for rec in df.to_dict(orient="records"):
        rows.append(
            models.APILog(
                api_id=by_endpoint[rec["endpoint"]],
                timestamp=rec["timestamp"].to_pydatetime(),
                status_code=int(rec["status_code"]),
                response_time_ms=float(rec["response_time_ms"]),
                request_count=int(rec["request_count"]),
                cpu_usage=float(rec["cpu_usage"]),
                db_latency_ms=float(rec["db_latency_ms"]),
            )
        )
    db.bulk_save_objects(rows)
    db.commit()

