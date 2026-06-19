# Reviewer Guide

This guide is intended for supervisors, second readers, and examiners who want
to inspect the repository as the applied counterpart to the research project
*Safeguarding Synthetic Agency*. The thesis explains the conceptual framework;
this repository shows how that framework is operationalized as a runnable
prototype, red-teaming module, and computational-analysis pipeline.

## Recommended Review Order

1. Read the root [README](../README.md) for setup, prerequisites, and the
   codebase-to-thesis relationship.
2. Open [Thesis To Code Map](thesis-code-map.md) to see how the six system
   integrity dimensions map to code modules, prompt families, saved data, and
   plots.
3. Start the app with `./start.sh` and open `http://127.0.0.1:3000`.
4. Use the **Chat** tab to compare guardrailed and lightweight persona replies.
5. Use the **Red-teaming** tab to inspect saved final reports or run a small
   one-profile evaluation.
6. Use the **Analysis** tab to regenerate plots from a saved final-results JSON
   file.
7. Review [Reference Dataset](reference-dataset.md) for the curated run used as
   a stable inspection target.

## Suggested Demo Flow

For a short live demonstration, use this sequence:

1. Start the app and select a persona.
2. Send an out-of-profile expert question in guardrailed chat, then compare with
   the lightweight mode.
3. Open Red-teaming and select an existing final report.
4. Expand one prompt case to compare the lightweight answer, guardrailed answer,
   score, and evaluator reasoning.
5. Open Analysis, select the same JSON report, and inspect:
   - Guardrail Effect Forest Plot
   - Pairwise Win Rate
   - Guardrail Delta Heatmap
   - Failure Transition Matrix
   - Performance-Stability Frontier

This path shows the core research claim in one pass: the same SSA profile is
tested with and without the full guardrail pipeline, and the result is measured
through paired red-team evaluation plus reproducible computational analysis.

## What Each Tab Demonstrates

| Tab | What To Look For | Thesis Relevance |
| --- | --- | --- |
| Chat | Profile-bounded responses, guardrailed/lightweight selector, message analysis metadata | Operationalizes SSA behavior and live guardrail inspection |
| Red-teaming | Single-turn adversarial prompt suite, profile selection, answer review, optional human score overrides | Turns PBAR, TBAR, EB, SFAM, SC, and PG into measurable evaluation dimensions |
| Analysis | Saved result selection, paired plots, distribution plots, downloads | Converts red-team reports into computational evidence for the findings chapter |

## Minimal Run For Reviewers

To avoid a long first evaluation, run only one or two profiles and a small
method selection. For the full thesis-style comparison, choose **Full analysis
stack** so each prompt is executed against both the lightweight baseline and the
guardrailed framework.

## Quick Verification

Run this after setup or before a review meeting:

```bash
bash scripts/smoke_check.sh
```

The smoke check compiles Python modules, checks expected backend routes, and
builds the frontend. It does not require a long red-team run.

## Reading Results

Saved red-team datasets live in:

```text
red_teaming/data/reports/
```

Generated computational-analysis artifacts live in:

```text
red_teaming/data/analysis/<run_id>/
```

The final-results JSON file is the canonical dataset. PDF reports and generated
plots are derived from that JSON.
