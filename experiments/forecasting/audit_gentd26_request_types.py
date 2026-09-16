from pathlib import Path

import pandas as pd


RAW_PATH = Path(
    "data/raw/gentd26/lora_request_trace.csv"
)


def main() -> None:
    df = pd.read_csv(RAW_PATH)

    df["gmt_create"] = pd.to_datetime(
        df["gmt_create"],
        errors="raise",
    )

    df["hour"] = df["gmt_create"].dt.floor("h")

    print("=" * 70)
    print("GenTD26 Dataset B — Request-Type / Zero-Hour Audit")
    print("=" * 70)

    # ---------------------------------------------------------------
    # 1. REQUEST TYPE COUNTS
    # ---------------------------------------------------------------

    print("\n=== REQUEST TYPE COUNTS ===")

    print(
        df["predict_type"]
        .value_counts()
        .to_string()
    )

    # ---------------------------------------------------------------
    # 2. HOURLY COUNTS BY REQUEST TYPE
    # ---------------------------------------------------------------

    print("\n=== HOURLY REQUEST COUNTS BY TYPE ===")

    type_hourly = pd.crosstab(
        df["hour"],
        df["predict_type"],
    )

    full_hours = pd.date_range(
        start=df["hour"].min(),
        end=df["hour"].max(),
        freq="h",
    )

    type_hourly = type_hourly.reindex(
        full_hours,
        fill_value=0,
    )

    print(
        type_hourly.head(24).to_string()
    )

    # ---------------------------------------------------------------
    # 3. ZERO HOURS BY REQUEST TYPE
    # ---------------------------------------------------------------

    print("\n=== ZERO HOURS BY REQUEST TYPE ===")

    for request_type in type_hourly.columns:
        zero_hours = (
            type_hourly[request_type] == 0
        ).sum()

        print(
            f"{request_type}: "
            f"{zero_hours} / {len(type_hourly)} "
            f"zero hours "
            f"({zero_hours / len(type_hourly):.2%})"
        )

    # ---------------------------------------------------------------
    # 4. 11:00–15:00 PATTERN
    # ---------------------------------------------------------------

    print("\n=== HOURS 09:00–16:00 BY REQUEST TYPE ===")

    type_hourly_with_hour = type_hourly.copy()
    type_hourly_with_hour["hour_of_day"] = (
        type_hourly_with_hour.index.hour
    )

    selected = (
        type_hourly_with_hour
        .groupby("hour_of_day")
        .agg(["mean", "median", "min", "max"])
    )

    selected_hours = [
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
    ]

    print(
        selected.loc[selected_hours].to_string()
    )

    # ---------------------------------------------------------------
    # 5. DAILY TOTALS BY TYPE
    # ---------------------------------------------------------------

    print("\n=== DAILY REQUEST TOTALS BY TYPE ===")

    daily_type = pd.crosstab(
        df["gmt_create"].dt.date,
        df["predict_type"],
    )

    print(
        daily_type.to_string()
    )

    # ---------------------------------------------------------------
    # 6. SIMULTANEOUS ZERO HOURS
    # ---------------------------------------------------------------

    print("\n=== SIMULTANEOUS ZERO HOURS ===")

    if len(type_hourly.columns) > 0:
        all_zero = (
            type_hourly.eq(0).all(axis=1)
        )

        print(
            "Hours where ALL request types are zero:",
            int(all_zero.sum()),
        )

        print(
            "Examples:"
        )

        print(
            type_hourly.loc[all_zero]
            .head(20)
            .to_string()
        )

    # ---------------------------------------------------------------
    # 7. SPECIFIC NOON CHECK
    # ---------------------------------------------------------------

    print("\n=== NOON CHECK ===")

    noon = type_hourly[
        type_hourly.index.hour == 12
    ]

    print(
        noon.to_string()
    )

    # ---------------------------------------------------------------
    # 8. STATUS BY REQUEST TYPE
    # ---------------------------------------------------------------

    print("\n=== STATUS BY REQUEST TYPE ===")

    status_type = pd.crosstab(
        df["predict_type"],
        df["predict_status"],
    )

    print(
        status_type.to_string()
    )

    print("\nAudit complete.")
    print("Raw Dataset B file was not modified.")


if __name__ == "__main__":
    main()