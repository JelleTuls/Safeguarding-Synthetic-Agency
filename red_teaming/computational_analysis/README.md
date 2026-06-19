# Computational Analysis

This module turns saved red-teaming JSON reports into reproducible tables,
figures, PNG exports, and PDF/Markdown summaries for the thesis
computational-analysis chapter. The goal is not only dashboard reporting, but a
paired computational evaluation of whether the full guardrailed SSA pipeline
improves system-integrity scores over the lightweight profile-only baseline.

The analysis is intentionally separated from the runner and frontend:

- `pipeline.py` loads final run JSON, computes derived metrics, and writes all
  artifacts.
- CSV tables are saved so figures can be recreated or checked in a spreadsheet.
- SVG figures are generated with the Python standard library, avoiding hidden
  plotting dependencies.
- PNG companion images and a visual ZIP bundle are generated for thesis writing.
- A manifest records generated files, warnings, figure groups, case counts,
  configuration, and analysis version.

Generated artifacts are written to:

```text
red_teaming/data/analysis/<run_id>/
```

Core outputs:

- `tables/case_level_results.csv`
- `tables/paired_case_deltas.csv`
- `tables/method_effect_summary.csv`
- `tables/round_stability_summary.csv`
- `tables/profile_effect_summary.csv`
- `tables/prompt_effect_summary.csv`
- `tables/bootstrap_ci_summary.csv`
- `tables/statistical_tests_summary.csv`
- `tables/failure_transition_matrix.csv`
- `tables/survival_table.csv`
- `tables/judge_human_calibration.csv`
- `tables/method_summary.csv`
- `tables/profile_summary.csv`
- `tables/eb_pairwise_examples.csv`
- `summaries/analysis_summary.md`
- `summaries/analysis_summary.pdf`
- `manifest.json`
- `<run_id>-computational-analysis.zip`
- `visual-analysis-bundle.zip`

## Required And Optional Fields

The module works with minimal final-results reports containing:

- `run_id`
- `cases`
- per-case `profile_id`, `method`, `prompt_id`, `target_mode`
- per-case `automated_score` or human override score

Optional fields improve the analysis when available:

- `round_id`, `round_label`, `round_type`
- `prompt_mutation_id`, `prompt_family`, `attack_family`
- evaluator metadata such as `llm_grade`, `comparison_grade`, and rationale
- guardrail metadata such as action, relevance, epistemic, subjectivity,
  objectivity, and persuasion scores
- `style_distance` and `adversarial_intensity`
- `human_review.score` and `human_review.notes`

Missing optional fields never crash analysis. They produce warnings in
`manifest.json` and `analysis_summary.md`.

## Main Formulas

The paired score delta is:

```text
delta_i,m,r = score_i,guardrailed,m,r - score_i,lightweight,m,r
```

For each method, the module reports:

- mean and median paired delta
- bootstrap 95% confidence interval for mean delta
- win, tie, and loss rates
- pass/failure rates at `tau = 0.75` by default
- relative failure reduction when the lightweight failure rate is non-zero
- Cohen's dz and rank-biserial effect size

Round stability uses `round_id` when at least two distinct rounds exist. If only
one round is available, round stability, EWMA, and survival figures are replaced
with explicit skipped-analysis plots and warnings.

## Figure Groups And Frontend Selection

The manifest groups figures for the frontend:

- Selected thesis figures shown by default: paired guardrail effect forest plot,
  pairwise win rate, failure transition matrix, score distributions boxplot,
  delta ECDF by method, performance-stability frontier, and guardrail delta
  heatmap.
- Diagnostic figures generated when data supports them: round stability,
  EWMA/control chart, survival curve, profile effect caterpillar, judge-human
  calibration, style drift, and Epistemic Boundary response surface.
- Descriptive figures generated for auditability: bar charts, heatmaps,
  distributions, radar plots, pass rates, consistency plots, and summary views.

Each figure has a manifest caption explaining what is compared, the sample size
or metric, and how to read the graph.

The frontend intentionally displays the selected thesis figures first so the
analysis tab supports the findings chapter rather than behaving like a generic
dashboard. Skipped figures are preserved as warnings in `manifest.json` and
`analysis_summary.md` when the required optional fields are absent.

The frontend calls the backend endpoint:

```text
POST /api/red-team/final-reports/{run_id}/analysis
```

Optional config:

```json
{
  "tau": 0.75,
  "n_boot": 10000,
  "seed": 42,
  "round_mode": "auto",
  "include_advanced": true
}
```

The endpoint regenerates artifacts from the saved final report. The Analysis tab
also exposes the full JSON dataset download, per-plot PNG downloads at selectable
pixel sizes, and a visual ZIP containing SVG plots, PNG plot images, and the PDF
summary.
