# Reference Dataset

This repository contains saved final-results reports and generated analysis
artifacts that can be used to inspect the system without running a new long
red-team evaluation.

## Curated Reference Run

The most useful current reference run is:

```text
rt-20260618-180138-af1204a6
```

Primary files:

```text
red_teaming/data/reports/rt-20260618-180138-af1204a6-final-results.json
red_teaming/data/reports/rt-20260618-180138-af1204a6-final-results.pdf
red_teaming/data/analysis/rt-20260618-180138-af1204a6/
```

This run contains 600 cases over 5 profiles, with paired lightweight and
guardrailed responses for the selected red-team prompt suite. It is useful as a
stable demonstration dataset because it has finalized scores, report exports,
and computational-analysis artifacts.

## Current Summary For The Reference Run

| Metric | Value |
| --- | ---: |
| Total cases | 600 |
| Paired guardrailed/lightweight cases | 300 |
| Guardrailed mean score | 0.826 |
| Lightweight mean score | 0.5555 |
| Overall paired delta | +0.2704 |
| Pairwise guardrailed win rate | 85% |
| Epistemic Boundary delta | +0.1201 |

Method-level paired deltas:

| Method | Guardrailed | Lightweight | Delta |
| --- | ---: | ---: | ---: |
| PBAR | 0.9727 | 0.6414 | +0.3313 |
| TBAR | 0.9247 | 0.6231 | +0.3017 |
| EB | 0.7437 | 0.6236 | +0.1201 |
| SFAM | 0.8266 | 0.7488 | +0.0778 |
| SC | 0.6940 | 0.3521 | +0.3419 |
| PG | 0.7941 | 0.3442 | +0.4499 |

## How To Inspect It In The App

1. Start the app with `./start.sh`.
2. Open `http://127.0.0.1:3000`.
3. Open **Red-teaming**.
4. Select the saved run ending in `af1204a6` to inspect answer pairs and scores.
5. Open **Analysis**.
6. Select `rt-20260618-180138-af1204a6-final-results.json`.
7. Regenerate analysis if needed.

Regenerating analysis overwrites the analysis folder for the same run, keeping
plots aligned with the currently saved JSON dataset.

## Data Warnings

This is a one-round report. It can support paired cross-sectional claims, but it
should not be used as evidence for true multi-round stability. The analysis
module records this warning in the generated manifest and summary.

The run also lacks paired `style_distance` and `adversarial_intensity` metadata,
so stylometric drift-by-intensity plots are skipped.
