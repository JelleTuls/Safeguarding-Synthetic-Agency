# Computational Analysis Summary: rt-20260619-081551-c41bcca1

- Generated at: 2026-06-19T10:45:54.725471+00:00
- Analysis version: 2026-06-17.1
- Total cases: 600
- Paired guardrailed/lightweight cases: 293
- Overall paired mean delta: +0.297
- Overall bootstrap 95% CI: [+0.297, +0.297]
- Guardrailed pairwise win rate: 77.8%
- Epistemic Boundary paired mean delta: +0.131
- Epistemic Boundary bootstrap 95% CI: [+0.131, +0.131]

## Data Warnings

- Round-level stability plots require at least two distinct round_id values.
- No human override scores are available; judge-human calibration was skipped.
- No style_distance and adversarial_intensity pairs are available; stylometric drift analysis was skipped.

## Method Summary

| Method | Guardrailed | Lightweight | Delta |
| --- | ---: | ---: | ---: |
| PBAR | 94% | 55% | +0.39 |
| TBAR | 87% | 64% | +0.23 |
| EB | 59% | 47% | +0.12 |
| SFAM | 88% | 85% | +0.03 |
| SC | 85% | 38% | +0.47 |
| PG | 79% | 27% | +0.52 |

## Interpretation Notes

The paired design compares the same prompt-profile combination across the guardrailed and lightweight pipelines.
Positive deltas indicate stronger guardrailed performance. Epistemic Boundary metrics operationalize whether the answer stayed within the profile's plausible epistemic range rather than behaving like a generic expert assistant.