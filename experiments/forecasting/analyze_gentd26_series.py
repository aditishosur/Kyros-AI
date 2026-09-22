from pathlib import Path

import pandas as pd


INPUT_PATH = Path(
    "data/processed/dataset_b_candidate/"
    "gentd26_hourly_request_counts.csv"
)


def find_zero_runs(df: pd.DataFrame) -> list[tuple[pd.Timestamp, pd.Timestamp, int]]:
    """
    Find consecutive runs of zero-request hours.
    """
    is_zero = df["request_count"].eq(0)

    groups = is_zero.ne(is_zero.shift()).cumsum()

    runs = []

    for _, group in df[is_zero].groupby(groups[is_zero]):
        start = group["timestamp"].iloc[0]
        end = group["timestamp"].iloc[-1]
        length = len(group)

        runs.append((start, end, length))

    return sorted(
        runs,
        key=lambda x: x[2],
        reverse=True,
    )


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Processed Dataset B file not found: {INPUT_PATH}"
        )

    df = pd.read_csv(INPUT_PATH)

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="raise",
    )

    df = df.sort_values("timestamp").reset_index(drop=True)

    print("=" * 70)
    print("GenTD26 Dataset B — Hourly Workload Diagnostic")
    print("=" * 70)

    # ------------------------------------------------------------------
    # 1. BASIC SERIES INFORMATION
    # ------------------------------------------------------------------

    print("\n=== SERIES OVERVIEW ===")

    print(f"Observations: {len(df):,}")
    print(f"Start:        {df['timestamp'].min()}")
    print(f"End:          {df['timestamp'].max()}")

    span_hours = (
        df["timestamp"].max()
        - df["timestamp"].min()
    ).total_seconds() / 3600

    print(f"Span:         {span_hours:.2f} hours")
    print(f"Total requests: {df['request_count'].sum():,}")

    # ------------------------------------------------------------------
    # 2. DISTRIBUTION
    # ------------------------------------------------------------------

    print("\n=== REQUEST COUNT DISTRIBUTION ===")

    print(
        df["request_count"].describe(
            percentiles=[
                0.10,
                0.25,
                0.50,
                0.75,
                0.90,
                0.95,
                0.99,
            ]
        )
    )

    print(
        f"\nZero-request hours: "
        f"{(df['request_count'] == 0).sum():,}"
    )

    print(
        f"Nonzero hours: "
        f"{(df['request_count'] > 0).sum():,}"
    )

    zero_fraction = (
        df["request_count"].eq(0).mean()
    )

    print(
        f"Zero-hour fraction: "
        f"{zero_fraction:.2%}"
    )

    # ------------------------------------------------------------------
    # 3. DAILY AGGREGATION
    # ------------------------------------------------------------------

    print("\n=== DAILY REQUEST TOTALS ===")

    daily = (
        df.set_index("timestamp")["request_count"]
        .resample("D")
        .agg(
            [
                "sum",
                "mean",
                "min",
                "max",
                "count",
            ]
        )
    )

    daily.columns = [
        "total_requests",
        "mean_hourly_requests",
        "min_hourly_requests",
        "max_hourly_requests",
        "hours",
    ]

    print(daily.to_string())

    print(
        f"\nNumber of calendar days: "
        f"{len(daily)}"
    )

    print(
        f"Days with zero total requests: "
        f"{(daily['total_requests'] == 0).sum()}"
    )

    # ------------------------------------------------------------------
    # 4. ZERO-HOUR RUNS
    # ------------------------------------------------------------------

    print("\n=== ZERO-REQUEST RUNS ===")

    zero_runs = find_zero_runs(df)

    print(
        f"Number of zero-request runs: "
        f"{len(zero_runs)}"
    )

    if zero_runs:
        print("\nLongest zero-request runs:")

        for start, end, length in zero_runs[:15]:
            print(
                f"  {start} -> {end} "
                f"({length} consecutive hours)"
            )

        longest = zero_runs[0]

        print(
            f"\nLongest zero run: "
            f"{longest[2]} hours"
        )

    # ------------------------------------------------------------------
    # 5. HOURLY PATTERN
    # ------------------------------------------------------------------

    print("\n=== HOUR-OF-DAY PATTERN ===")

    hourly_pattern = (
        df.assign(
            hour=df["timestamp"].dt.hour
        )
        .groupby("hour")["request_count"]
        .agg(
            [
                "count",
                "mean",
                "median",
                "min",
                "max",
                lambda x: (x == 0).sum(),
            ]
        )
    )

    hourly_pattern.columns = [
        "observations",
        "mean_requests",
        "median_requests",
        "min_requests",
        "max_requests",
        "zero_hours",
    ]

    print(hourly_pattern.to_string())

    # ------------------------------------------------------------------
    # 6. DAY-OF-WEEK PATTERN
    # ------------------------------------------------------------------

    print("\n=== DAY-OF-WEEK PATTERN ===")

    weekday_pattern = (
        df.assign(
            day_of_week=df["timestamp"].dt.day_name()
        )
        .groupby("day_of_week")["request_count"]
        .agg(
            [
                "count",
                "mean",
                "median",
                "min",
                "max",
                lambda x: (x == 0).sum(),
            ]
        )
    )

    weekday_pattern.columns = [
        "observations",
        "mean_requests",
        "median_requests",
        "min_requests",
        "max_requests",
        "zero_hours",
    ]

    weekday_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    weekday_pattern = weekday_pattern.reindex(
        weekday_order
    )

    print(weekday_pattern.to_string())

    # ------------------------------------------------------------------
    # 7. TEMPORAL GAPS
    # ------------------------------------------------------------------

    print("\n=== TEMPORAL GAP CHECK ===")

    gaps = (
        df["timestamp"]
        .sort_values()
        .diff()
        .dropna()
    )

    print(
        "All gaps exactly 1 hour:",
        bool(
            (gaps == pd.Timedelta(hours=1)).all()
        ),
    )

    print(
        "Largest timestamp gap:",
        gaps.max(),
    )

    # ------------------------------------------------------------------
    # 8. SPLIT SUMMARY
    # ------------------------------------------------------------------

    print("\n=== FROZEN 60/20/20 SPLIT ===")

    n = len(df)

    train_end = round(n * 0.60)

    validation_end = (
        train_end + round(n * 0.20)
    )

    splits = {
        "TRAIN": df.iloc[:train_end],
        "VALIDATION": df.iloc[
            train_end:validation_end
        ],
        "TEST": df.iloc[validation_end:],
    }

    for name, split in splits.items():
        print(f"\n{name}")

        print(
            f"  Hours: {len(split)}"
        )

        print(
            f"  Start: {split['timestamp'].min()}"
        )

        print(
            f"  End:   {split['timestamp'].max()}"
        )

        print(
            f"  Total requests: "
            f"{split['request_count'].sum():,}"
        )

        print(
            f"  Mean hourly requests: "
            f"{split['request_count'].mean():.2f}"
        )

        print(
            f"  Zero-request hours: "
            f"{(split['request_count'] == 0).sum()}"
        )

    # ------------------------------------------------------------------
    # 9. SPLIT DISTRIBUTION COMPARISON
    # ------------------------------------------------------------------

    print("\n=== SPLIT DISTRIBUTION COMPARISON ===")

    for name, split in splits.items():
        print(
            f"{name:12s} "
            f"mean={split['request_count'].mean():8.2f}  "
            f"median={split['request_count'].median():6.1f}  "
            f"max={split['request_count'].max():4d}  "
            f"zero={split['request_count'].eq(0).mean():6.2%}"
        )

    # ------------------------------------------------------------------
    # 10. EXTREME HOURS
    # ------------------------------------------------------------------

    print("\n=== HIGHEST-WORKLOAD HOURS ===")

    highest = (
        df.nlargest(
            10,
            "request_count",
        )
        [["timestamp", "request_count"]]
    )

    print(highest.to_string(index=False))

    print("\n=== LOWEST NONZERO HOURS ===")

    lowest_nonzero = (
        df[df["request_count"] > 0]
        .nsmallest(
            10,
            "request_count",
        )
        [["timestamp", "request_count"]]
    )

    print(
        lowest_nonzero.to_string(
            index=False
        )
    )

    # ------------------------------------------------------------------
    # 11. FINAL DIAGNOSTIC SUMMARY
    # ------------------------------------------------------------------

    print("\n" + "=" * 70)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 70)

    checks = {
        "554 hourly observations": len(df) == 554,
        "26,823 total requests preserved": (
            df["request_count"].sum() == 26823
        ),
        "No duplicate timestamps": (
            df["timestamp"].nunique() == len(df)
        ),
        "Continuous hourly timestamps": (
            (gaps == pd.Timedelta(hours=1)).all()
        ),
        "No missing request counts": (
            df["request_count"].notna().all()
        ),
        "No negative request counts": (
            (df["request_count"] >= 0).all()
        ),
        "No completely empty calendar days": (
            (daily["total_requests"] > 0).all()
        ),
        "Correct train size": (
            len(splits["TRAIN"]) == 332
        ),
        "Correct validation size": (
            len(splits["VALIDATION"]) == 111
        ),
        "Correct test size": (
            len(splits["TEST"]) == 111
        ),
    }

    for check, passed in checks.items():
        print(
            f"{'PASS' if passed else 'FAIL':4s} | {check}"
        )

    print("\nNo forecasting models were run.")
    print("No data was modified by this script.")


if __name__ == "__main__":
    main()