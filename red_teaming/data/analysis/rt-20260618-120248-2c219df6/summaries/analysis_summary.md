# Computational Analysis Summary: rt-20260618-120248-2c219df6

- Generated at: 2026-06-18T14:02:43.347311+00:00
- Analysis version: 2026-06-17.1
- Total cases: 600
- Paired guardrailed/lightweight cases: 292
- Overall paired mean delta: +0.244
- Overall bootstrap 95% CI: [+0.244, +0.244]
- Guardrailed pairwise win rate: 59.2%
- Epistemic Boundary paired mean delta: +0.113
- Epistemic Boundary bootstrap 95% CI: [+0.113, +0.113]

## Data Warnings

- Round-level stability plots require at least two distinct round_id values.
- No human override scores are available; judge-human calibration was skipped.
- No style_distance and adversarial_intensity pairs are available; stylometric drift analysis was skipped.

## Method Summary

| Method | Guardrailed | Lightweight | Delta |
| --- | ---: | ---: | ---: |
| PBAR | 90% | 91% | -0.01 |
| TBAR | 91% | 76% | +0.15 |
| EB | 80% | 70% | +0.10 |
| SFAM | 90% | 76% | +0.14 |
| SC | 76% | 29% | +0.46 |
| PG | 85% | 26% | +0.59 |

## Interpretation Notes

The paired design compares the same prompt-profile combination across the guardrailed and lightweight pipelines.
Positive deltas indicate stronger guardrailed performance. Epistemic Boundary metrics operationalize whether the answer stayed within the profile's plausible epistemic range rather than behaving like a generic expert assistant.