# Computational Analysis Summary: rt-20260618-093056-b82b224b

- Generated at: 2026-06-18T11:36:27.953376+00:00
- Analysis version: 2026-06-17.1
- Total cases: 600
- Paired guardrailed/lightweight cases: 299
- Overall paired mean delta: +0.192
- Overall bootstrap 95% CI: [+0.192, +0.192]
- Guardrailed pairwise win rate: 57.5%
- Epistemic Boundary paired mean delta: +0.213
- Epistemic Boundary bootstrap 95% CI: [+0.212, +0.212]

## Data Warnings

- Round-level stability plots require at least two distinct round_id values.
- No human override scores are available; judge-human calibration was skipped.
- No style_distance and adversarial_intensity pairs are available; stylometric drift analysis was skipped.

## Method Summary

| Method | Guardrailed | Lightweight | Delta |
| --- | ---: | ---: | ---: |
| PBAR | 86% | 92% | -0.06 |
| TBAR | 89% | 75% | +0.13 |
| EB | 85% | 64% | +0.21 |
| SFAM | 85% | 82% | +0.03 |
| SC | 66% | 31% | +0.35 |
| PG | 71% | 23% | +0.48 |

## Interpretation Notes

The paired design compares the same prompt-profile combination across the guardrailed and lightweight pipelines.
Positive deltas indicate stronger guardrailed performance. Epistemic Boundary metrics operationalize whether the answer stayed within the profile's plausible epistemic range rather than behaving like a generic expert assistant.