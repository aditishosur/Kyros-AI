# Research Repository Layout

The existing `backend/` and `frontend/` directories are the Kyros product and demonstration layer. Research evidence is produced only by offline scripts and stored artifacts.

| Path | Purpose |
| --- | --- |
| `experiments/common/` | Split validation, run metadata, and handoff helpers. |
| `experiments/scenarios/` | Controlled synthetic telemetry, scenario taxonomy, and ground-truth manifests. |
| `experiments/anomaly/` | Detector fitting, scoring, event-level evaluation, figures, and Dataset B adaptation. |
| `configs/` | Frozen experiment configuration before final test evaluation. |
| `data/raw/` | Original external files. Never overwrite them. |
| `data/processed/` | Derived telemetry and Dataset B mappings. |
| `data/manifests/` | Frozen scenario manifests when retained separately from run output. |
| `results/<run_id>/` | Reproducible metrics, scores, figures, metadata, and team handoff for a single run. |
| `docs/protocol/` | Research decisions and evaluation conventions. |
| `docs/data_dictionary/` | Cause vocabulary and external-data column mappings. |
| `tests/` | Unit tests for scenario injection, splits, and alert evaluation. |

Every final number must be traceable to a run ID, configuration hash, input hash, and stored result artifact.
