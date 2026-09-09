from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_commit(project_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=project_root, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def write_run_metadata(output_path: Path, config_path: Path, input_path: Path) -> None:
    metadata = {
        "run_id": output_path.parent.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit(Path.cwd()),
        "config_path": str(config_path),
        "config_sha256": file_sha256(config_path),
        "input_path": str(input_path),
        "input_sha256": file_sha256(input_path),
    }
    output_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def write_daily_handoff(output_path: Path, run_id: str, command: str, input_path: Path, result_files: list[Path]) -> None:
    """Create the team handoff record required for every reproducible run."""
    handoff = f"""# Daily Kyros Research Handoff

Owner: Aditi
Date: {datetime.now(timezone.utc).date().isoformat()}
Git branch / commit: {git_commit(Path.cwd())}
What I completed: Controlled anomaly evaluation run created.
Exact command to reproduce: `{command}`
Input dataset + hash/version: `{input_path}`; SHA-256 `{file_sha256(input_path)}`
Run ID(s): {run_id}
Result files:
{chr(10).join(f'- `{path}`' for path in result_files)}
Key metric(s): See `metrics/anomaly_metrics.csv`.
What failed / limitation: Dataset B does not support the full multivariate feature set or warning lead-time interpretation unless its semantics are verified.
What I need from another teammate: Amulya must confirm that the frozen cause taxonomy matches the RCA output vocabulary.
Can another teammate reproduce this? Yes, after installing the locked project requirements.
"""
    output_path.write_text(handoff, encoding="utf-8")
