# Reproducibility Checklist

Use this checklist to recreate the local application and regenerate analysis
artifacts from saved red-team reports.

## Setup Checklist

- Install Python 3.11+.
- Install Node.js 18+ or current LTS.
- Install Docker Desktop and keep it running for full Layer 08 fidelity.
- Clone or open this repository.
- Copy the environment examples:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

- Fill one provider block in `backend/.env`.
- Keep `LLM_PROVIDER=auto` unless intentionally forcing a provider.
- Start the local stack:

```bash
./start.sh
```

- Open `http://127.0.0.1:3000`.

## Functional Checklist

- Chat tab loads the 30 cached personas.
- A persona can be selected and opened.
- Guardrailed and lightweight chat modes are selectable.
- Red-teaming tab can start or connect to the red-team service on port `8010`.
- Saved final reports appear in Red-teaming and Analysis views.
- Analysis can regenerate plots from a final-results JSON report.

## Short Reproducible Evaluation

For a quick smoke-style evaluation:

1. Open **Red-teaming**.
2. Select one profile.
3. Select one or two methods.
4. Select **Full analysis stack**.
5. Start the run.
6. Wait until the run completes.
7. Save/finalize the report.
8. Open **Analysis** and select the new JSON report.
9. Click **Generate analysis**.

This creates a new final-results JSON/PDF pair and an analysis artifact folder
under `red_teaming/data/analysis/<run_id>/`.

## Full Thesis-Style Evaluation

For thesis-like outputs:

- Select multiple profiles.
- Select all six methods: PBAR, TBAR, EB, SFAM, SC, and PG.
- Use **Full analysis stack** so lightweight and guardrailed responses are
  paired.
- Review or override scores only where human adjudication is desired.
- Finalize the run.
- Generate computational analysis from the saved report.

## Verification Command

Run:

```bash
bash scripts/smoke_check.sh
```

The smoke check compiles backend and red-team Python modules, verifies expected
FastAPI routes, and builds the frontend. It is a build/regression check, not a
replacement for running the red-team evaluation itself.

## Reproducibility Notes

- The generated SSA profiles are cached in `backend/app/data/`.
- Saved final-results JSON files are the canonical datasets.
- Computational-analysis folders can be regenerated from the saved JSON files.
- One-round reports cannot produce true round-level stability claims. The
  analysis module records this as a warning instead of fabricating stability.
- LLM outputs and LLM-as-judge scores can vary by provider/model, so provider
  configuration should be reported with any new result set.
