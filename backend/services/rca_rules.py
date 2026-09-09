"""Pure rule-based root-cause decision logic used by Kyros."""


def determine_root_cause(
    traffic: float,
    db_latency: float,
    errors: float,
) -> tuple[str, str]:
    """Apply Kyros's rule-based RCA decision logic."""

    if traffic > 25 and db_latency > 15:
        return (
            "Database pressure caused by traffic surge",
            "Increase service capacity and inspect database saturation before the next traffic peak.",
        )

    if db_latency > 25:
        return (
            "Database latency is the primary degradation driver",
            "Investigate slow queries, connection pool saturation and database resource limits.",
        )

    if errors > 5:
        return (
            "Application error burst",
            "Review recent deploys and error logs for elevated 5xx responses.",
        )

    return (
        "Elevated performance risk",
        "Continue monitoring and validate capacity headroom.",
    )
