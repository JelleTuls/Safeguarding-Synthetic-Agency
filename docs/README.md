# Documentation Index

This folder collects the project documentation in one place. The root
`README.md` remains the main setup and quick-start file; the documents below
explain specific parts of the system.

## Runtime And Architecture

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
  frontend startup notes.

## For Teachers And Reviewers

Start with [SSA Guardrail Flow](ssa-guardrail-flow.md) for the thesis-facing
architecture, then read [Guardrail Framework](guardrail-framework.md) for the
layer-by-layer design and [Red-Teaming Service](red-teaming-service.md) for the
evaluation method.

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
  prompt suites, LLM grading, human mediation, and final scoring.

## Supporting Services

- [Subjectivity Classifier Sidecar](subjectivity-classifier-sidecar.md):
  Dockerized `fractalego/subjectivity_classifier` service, optional GloVe file,
  API shape, and backend hook.
