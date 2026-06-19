# Computational Analysis Summary: rt-20260618-180138-af1204a6

- Generated at: 2026-06-19T08:05:11.064426+00:00
- Analysis version: 2026-06-17.1
- Total cases: 600
- Paired guardrailed/lightweight cases: 300
- Overall paired mean delta: +0.270
- Overall bootstrap 95% CI: [+0.270, +0.270]
- Guardrailed pairwise win rate: 83.0%
- Epistemic Boundary paired mean delta: +0.120
- Epistemic Boundary bootstrap 95% CI: [+0.120, +0.120]

## Data Warnings

- Round-level stability plots require at least two distinct round_id values.
- No style_distance and adversarial_intensity pairs are available; stylometric drift analysis was skipped.

## Method Summary

| Method | Guardrailed | Lightweight | Delta |
| --- | ---: | ---: | ---: |
| PBAR | 97% | 64% | +0.33 |
| TBAR | 92% | 62% | +0.30 |
| EB | 74% | 62% | +0.12 |
| SFAM | 83% | 75% | +0.08 |
| SC | 69% | 35% | +0.34 |
| PG | 79% | 34% | +0.45 |

## Interpretation Notes

The paired design compares the same prompt-profile combination across the guardrailed and lightweight pipelines.
Positive deltas indicate stronger guardrailed performance. Epistemic Boundary metrics operationalize whether the answer stayed within the profile's plausible epistemic range rather than behaving like a generic expert assistant.