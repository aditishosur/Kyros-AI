from pathlib import Path

import pandas as pd


INPUT_PATH = Path(
    "data/processed/dataset_b_candidate/"
    "gentd26_hourly_request_counts.csv"
)


def main() -> None:
    df = pd.read_csv(INPUT_PATH)

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="raise",
    )

    print("\n=== BASIC STRUCTURE ===")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {list(df.columns)}")
    print(f"Duplicate rows: {df.duplicated().sum()}")

    print("\n=== TIMESTAMPS ===")
    print(f"First: {df['timestamp'].min()}")
    print(f"Last:  {df['timestamp'].max()}")
    print(
        "Unique timestamps:",
        df["timestamp"].nunique(),
    )

    print("\n=== CONTINUITY ===")
    differences = (
        df["timestamp"]
        .sort_values()
        .diff()
        .dropna()
    )

    print(
        "Unique timestamp gaps:",
        differences.value_counts().head(10),
    )

    expected_gap = pd.Timedelta(hours=1)

    print(
        "All gaps exactly 1 hour:",
        bool((differences == expected_gap).all()),
    )

    print("\n=== REQUEST COUNTS ===")
    print(
        "Total requests:",
        int(df["request_count"].sum()),
    )

    print(
        "Minimum hourly count:",
        int(df["request_count"].min()),
    )

    print(
        "Maximum hourly count:",
        int(df["request_count"].max()),
    )

    print(
        "Zero-request hours:",
        int((df["request_count"] == 0).sum()),
    )

    print(
        "Nonzero hours:",
        int((df["request_count"] > 0).sum()),
    )

    print("\n=== NULLS ===")
    print(df.isna().sum())

    print("\n=== NEGATIVE VALUES ===")
    print(
        "Negative request counts:",
        int((df["request_count"] < 0).sum()),
    )

    print("\n=== 60/20/20 SPLIT ===")

    n = len(df)

    train_end = round(n * 0.60)

    validation_end = (
        train_end + round(n * 0.20)
    )

    train = df.iloc[:train_end]
    validation = df.iloc[
        train_end:validation_end
    ]
    test = df.iloc[validation_end:]

    for name, split in [
        ("TRAIN", train),
        ("VALIDATION", validation),
        ("TEST", test),
    ]:
        print(f"\n{name}")
        print(f"Hours: {len(split)}")
        print(f"Start: {split['timestamp'].min()}")
        print(f"End:   {split['timestamp'].max()}")
        print(
            "Requests:",
            int(split["request_count"].sum()),
        )
        print(
            "Zero hours:",
            int(
                (split["request_count"] == 0).sum()
            ),
        )

    print("\n=== BOUNDARY CHECK ===")

    print(
        "Train < Validation:",
        train["timestamp"].max()
        < validation["timestamp"].min(),
    )

    print(
        "Validation < Test:",
        validation["timestamp"].max()
        < test["timestamp"].min(),
    )


if __name__ == "__main__":
    main()