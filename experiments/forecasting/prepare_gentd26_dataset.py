
from pathlib import Path

import pandas as pd


RAW_PATH = Path("data/raw/gentd26/lora_request_trace.csv")
OUTPUT_PATH = Path(
    "data/processed/dataset_b_candidate/"
    "gentd26_hourly_request_counts.csv"
)


def aggregate_hourly_request_counts(raw: pd.DataFrame) -> pd.DataFrame:
    """Aggregate every raw gmt_create record into continuous hourly counts."""
    if "gmt_create" not in raw.columns:
        raise ValueError("Missing required column: gmt_create")

    timestamps = pd.to_datetime(
        raw["gmt_create"],
        errors="coerce",
    )

    if timestamps.isna().any():
        raise ValueError(
            "Found invalid or missing gmt_create timestamps."
        )

    hourly = (
        timestamps
        .dt.floor("h")
        .value_counts()
        .sort_index()
        .rename("request_count")
        .to_frame()
    )

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
    return hourly.reset_index()


def main() -> None:
    raw = pd.read_csv(RAW_PATH)

    # All raw rows are included. No filtering is applied to
    # predict_type or predict_status.
    output = aggregate_hourly_request_counts(raw)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    output.to_csv(OUTPUT_PATH, index=False)

    print(f"Input rows: {len(raw):,}")
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