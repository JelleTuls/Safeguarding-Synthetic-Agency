# Computational Analysis Summary: rt-20260615-143335-e6b33f15

- Generated at: 2026-06-18T08:57:12.168111+00:00
- Analysis version: 2026-06-17.1
- Total cases: 600
- Paired guardrailed/lightweight cases: 300
- Overall paired mean delta: +0.277
- Overall bootstrap 95% CI: [+0.277, +0.277]
- Guardrailed pairwise win rate: 83.3%
- Epistemic Boundary paired mean delta: +0.362
- Epistemic Boundary bootstrap 95% CI: [+0.362, +0.362]

## Data Warnings

- Round-level stability plots require at least two distinct round_id values.
- No style_distance and adversarial_intensity pairs are available; stylometric drift analysis was skipped.

## Method Summary

| Method | Guardrailed | Lightweight | Delta |
| --- | ---: | ---: | ---: |
| PBAR | 69% | 57% | +0.12 |
| TBAR | 74% | 53% | +0.21 |
| EB | 89% | 53% | +0.36 |
| SFAM | 86% | 55% | +0.31 |
| SC | 59% | 33% | +0.26 |
| PG | 69% | 29% | +0.40 |

## Interpretation Notes

The paired design compares the same prompt-profile combination across the guardrailed and lightweight pipelines.
Positive deltas indicate stronger guardrailed performance. Epistemic Boundary metrics operationalize whether the answer stayed within the profile's plausible epistemic range rather than behaving like a generic expert assistant.