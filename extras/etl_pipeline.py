"""
Kyros ETL Demonstration
Extract → Transform → Load pipeline for API telemetry.
"""

import sqlite3
import pandas as pd


INPUT_FILE = "api_telemetry.csv"
DB_FILE = "kyros_etl.db"


def extract():
    """Extract telemetry from CSV."""
    return pd.read_csv(INPUT_FILE)


def transform(df):
    """Clean and transform telemetry data."""

    df = df.copy()

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    df["response_time_ms"] = pd.to_numeric(
        df["response_time_ms"],
        errors="coerce"
    )

    df["error_rate"] = pd.to_numeric(
        df["error_rate"],
        errors="coerce"
    )

    df = df.dropna(subset=["timestamp"])

    # Derived metric used by analytics.
    df["performance_score"] = (
        100
        - (df["response_time_ms"].fillna(0) / 10)
        - (df["error_rate"].fillna(0) * 100)
    ).clip(lower=0, upper=100)

    return df


def load(df):
    """Load transformed data into SQL database."""

    conn = sqlite3.connect(DB_FILE)

    df.to_sql(
        "api_telemetry",
        conn,
        if_exists="replace",
        index=False
    )

    conn.close()


def run_pipeline():
    print("Extracting telemetry...")
    data = extract()

    print("Transforming telemetry...")
    transformed = transform(data)

    print("Loading into SQL...")
    load(transformed)

    print("ETL pipeline completed successfully.")


if __name__ == "__main__":
    run_pipeline()