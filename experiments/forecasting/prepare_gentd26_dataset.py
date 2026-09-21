from pathlib import Path

import pandas as pd


RAW_PATH = Path("data/raw/gentd26/lora_request_trace.csv")
OUTPUT_PATH = Path(
    "data/processed/dataset_b_candidate/"
    "gentd26_hourly_request_counts.csv"
)


def main() -> None:
    df = pd.read_csv(RAW_PATH)

    required_columns = {
        "gmt_create",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    timestamps = pd.to_datetime(
        df["gmt_create"],
        errors="coerce",
    )

    if timestamps.isna().any():
        raise ValueError(
            "Found invalid or missing gmt_create timestamps."
        )

    # Aggregate every raw request-arrival record into hourly counts.
    # All request types and predict_status values are intentionally included.
    # No filtering is applied.
    hourly = (
        timestamps
        .dt.floor("h")
        .value_counts()
        .sort_index()
        .rename("request_count")
        .to_frame()
    )

    # Reindex to a continuous hourly calendar.
    full_index = pd.date_range(
        start=hourly.index.min(),
        end=hourly.index.max(),
        freq="h",
    )

    hourly = hourly.reindex(
        full_index,
        fill_value=0,
    )

    hourly.index.name = "timestamp"

    output = hourly.reset_index()

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(f"Input rows: {len(df):,}")
    print(
        f"Input time range: "
        f"{timestamps.min()} -> {timestamps.max()}"
    )
    print(f"Hourly bins: {len(output):,}")
    print(
        f"Total requests in hourly series: "
        f"{output['request_count'].sum():,}"
    )
    print(
        f"Zero-request hours: "
        f"{(output['request_count'] == 0).sum():,}"
    )
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()