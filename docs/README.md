# Documentation Index

This folder collects the project documentation in one place. The root
`README.md` remains the main setup and quick-start file; the documents below
explain specific parts of the system.

## Runtime And Architecture

- [Reviewer Guide](reviewer-guide.md): suggested reading and demo path for
  supervisors, second readers, and examiners.
- [Reproducibility Checklist](reproducibility-checklist.md): clean-machine setup,
  short evaluation run, full thesis-style evaluation, and smoke check.
- [GitHub Branch Rules And Repository Protections](github-protections.md):
  recommended main/dev rulesets, required checks, and security settings.
- [Thesis To Code Map](thesis-code-map.md): maps SSA integrity dimensions to
  code modules, prompt families, saved data, and plots.
- [Reference Dataset](reference-dataset.md): curated saved run and analysis
  artifacts that can be inspected without creating a new long run.
- [SSA Guardrail Flow](ssa-guardrail-flow.md): simplified thesis-facing flow
  from user message to final validated response.
- [Backend Runtime](backend-runtime.md): backend package structure, persona
  loading, biography generation, provider configuration, and chat entry points.
- [Project Architecture](project-architecture.md): runtime boundaries, feature
  folders, guardrail pipeline ownership, and the smoke-check workflow.
- [Model Provider Configuration](model-provider-configuration.md): how to use
  one API key, one endpoint URL, and a user-selected model without requiring a
  Groq fallback.
- [Frontend Interface](frontend-interface.md): React chat interface and basic
  frontend startup notes for the Chat, Red-teaming, and Computational analysis
  tabs.

## Source File Documentation

The first-party source files in `backend/`, `frontend/src/`, `red_teaming/`,
`services/subjectivity_classifier/`, and `scripts/` include top-of-file
descriptions. Python modules use module docstrings, JavaScript files use compact
file headers, and shell scripts document their purpose below the shebang. These
headers are intended as quick orientation for reviewers reading the code beside
the thesis diagrams.

## For Teachers And Reviewers

Start with [Reviewer Guide](reviewer-guide.md) for a short handoff path through
the repository. Then read [Thesis To Code Map](thesis-code-map.md) to connect
the paper's concepts to implementation surfaces, [SSA Guardrail Flow](ssa-guardrail-flow.md)
for the thesis-facing architecture, [Guardrail Framework](guardrail-framework.md)
for the layer-by-layer design, and [Red-Teaming Service](red-teaming-service.md)
for the evaluation method. The reproducible thesis-plot package is documented in
[Computational Analysis](../red_teaming/computational_analysis/README.md).

Public artifact metadata lives at the repository root:

- [License](../LICENSE)
- [Citation metadata](../CITATION.cff)
- [Security policy](../SECURITY.md)
- [Contribution guide](../CONTRIBUTING.md)
- [Release notes](../RELEASE_NOTES.md)

## For Users Pulling The Package

Start with the root `README.md`, then use
[Model Provider Configuration](model-provider-configuration.md) and
[Subjectivity Classifier Sidecar](subjectivity-classifier-sidecar.md) if setup
questions come up. [Frontend Interface](frontend-interface.md) explains the
buttons and inspection surfaces in the app.

## Guardrails And Evaluation

- [Guardrail Framework](guardrail-framework.md): detailed explanation of the
  layered guardrail pipeline, calculations, validation logic, and inspection
  metadata.
- [Red-Teaming Service](red-teaming-service.md): standalone red-teaming service,
  prompt suites, LLM grading, pairwise guardrailed-vs-lightweight comparison,
  optional human mediation, and final scoring.
- [Computational Analysis](../red_teaming/computational_analysis/README.md):
  saved final-results JSON reports, paired guardrail-effect metrics, thesis
  figures, plot downloads, and reproducible artifact folders.
- [Limitations And Third-Party Components](limitations-and-citations.md):
  reviewer-facing limitations, external packages, and citation/reporting notes.

## Supporting Services

- [Subjectivity Classifier Sidecar](subjectivity-classifier-sidecar.md):
  Dockerized `fractalego/subjectivity_classifier` service, optional GloVe file,
  API shape, and backend hook.
