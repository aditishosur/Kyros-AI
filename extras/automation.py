"""
Kyros Automation Demonstration
Automated API health monitoring and report generation.
"""

from datetime import datetime
from pathlib import Path

import requests


API_BASE_URL = "http://localhost:8000"
REPORT_FILE = Path("kyros_health_report.txt")


def check_health():
    """Check whether the Kyros API is available."""

    try:
        response = requests.get(
            f"{API_BASE_URL}/health",
            timeout=5
        )

        return {
            "status": "UP" if response.ok else "DEGRADED",
            "http_status": response.status_code
        }

    except requests.RequestException:
        return {
            "status": "DOWN",
            "http_status": None
        }


def generate_report(result):
    """Generate an automated health report."""

    timestamp = datetime.now().isoformat()

    report = f"""
KYROS AUTOMATED HEALTH REPORT
=============================
Timestamp: {timestamp}
Service Status: {result["status"]}
HTTP Status: {result["http_status"]}
"""

    REPORT_FILE.write_text(report.strip())


def run_automation():
    """Execute the automated monitoring workflow."""

    result = check_health()
    generate_report(result)

    print(
        f"Automation completed. "
        f"Service status: {result['status']}"
    )


if __name__ == "__main__":
    run_automation()