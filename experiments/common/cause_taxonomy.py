"""Shared cause taxonomy for Kyros research experiments.

These labels are experiment identifiers, not claims of causal discovery.
"""

TRAFFIC_DB_PRESSURE = "TRAFFIC_DB_PRESSURE"
DB_LATENCY = "DB_LATENCY"
APPLICATION_ERROR = "APPLICATION_ERROR"
ELEVATED_RISK = "ELEVATED_RISK"

CAUSE_LABELS = (
    TRAFFIC_DB_PRESSURE,
    DB_LATENCY,
    APPLICATION_ERROR,
    ELEVATED_RISK,
)

KYROS_RCA_TO_LABEL = {
    "Database pressure caused by traffic surge": TRAFFIC_DB_PRESSURE,
    "Database latency is the primary degradation driver": DB_LATENCY,
    "Application error burst": APPLICATION_ERROR,
    "Elevated performance risk": ELEVATED_RISK,
}


def normalize_kyros_cause(cause: str) -> str:
    """Convert the human-readable Kyros RCA output to an experiment label."""
    if cause not in KYROS_RCA_TO_LABEL:
        raise ValueError(f"Unknown Kyros RCA output: {cause!r}")
    return KYROS_RCA_TO_LABEL[cause]
