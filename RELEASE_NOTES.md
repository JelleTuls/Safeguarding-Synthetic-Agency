# Release Notes

## v1.0-thesis-artifact - 2026-06-19

This release is the thesis-facing public artifact for *Safeguarding Synthetic
Agency: A Framework for Measuring and Operationalizing System Integrity in
Synthetic Social Agent Systems*.

## Included

- Persona chat interface for cached synthetic social agent profiles.
- Guardrailed SSA generation pipeline and lightweight profile-only baseline.
- Red-teaming workspace for selected profiles and single-turn prompt suites.
- Optional human score review and saved JSON/PDF final reports.
- Computational-analysis workspace for regenerating thesis-ready plots from
  saved final-results JSON files.
- Curated reference dataset:
  `red_teaming/data/reports/rt-20260618-180138-af1204a6-final-results.json`
- Curated analysis artifacts:
  `red_teaming/data/analysis/rt-20260618-180138-af1204a6/`

## Reproducibility Notes

- `./start.sh` is the preferred one-command local launcher.
- `bash scripts/prepare_project.sh` prepares env files and dependencies without
  starting long-running services.
- `bash scripts/smoke_check.sh` compiles backend/red-team Python and builds the
  frontend.
- Full Layer 08 subjectivity-classifier fidelity requires Docker Compose.
  Without Docker, the app starts with the deterministic subjectivity fallback.

## Known Limitations

- The included reference dataset is a one-round red-team report. It supports
  paired cross-sectional guardrailed-vs-lightweight claims, but not true
  multi-round stability claims.
- LLM-as-judge scores are useful for structured comparison but are not a
  substitute for formal human evaluation.
- Runtime behavior can differ when users change model providers, model versions,
  API endpoints, prompt settings, or scoring calibration examples.
- The system is a research prototype, not a production safety product.
