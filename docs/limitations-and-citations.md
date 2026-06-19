# Limitations And Third-Party Components

This document records practical limitations and external components that matter
when reviewing or reproducing the prototype.

## Current Limitations

- **Research prototype:** the repository is a local thesis prototype rather than
  a production deployment.
- **Single-turn red-teaming:** the current prompt suite uses single-turn attacks.
  It does not yet implement multi-turn or adaptive attack strategies.
- **LLM-as-judge dependency:** automated scores depend on the configured
  evaluator model. Human overrides are available, but a new model/provider can
  shift automated score distributions.
- **Provider variability:** generated answers vary by model, provider, and
  inference behavior. Saved final-results JSON files should be treated as the
  canonical datasets for reported plots.
- **Docker fallback mode:** if Docker is unavailable, the subjectivity
  classifier falls back to deterministic scoring. This keeps the pipeline usable
  but is not the highest-fidelity Layer 08 mode.
- **One-round stability:** round-level stability plots require multiple
  distinct `round_id` values. One-round reports support paired comparison, not
  longitudinal stability claims.
- **Stylometric drift metadata:** advanced style-distance plots require
  `style_distance` and `adversarial_intensity` fields. The analysis module skips
  those plots when the data are absent.
- **No real user study:** the app evaluates synthetic profiles and model
  responses; it is not a human-subject study of real voter behavior.

## External Components

| Component | Role |
| --- | --- |
| FastAPI / Uvicorn | Backend and red-team API services |
| React | Frontend chat, red-team review, and analysis interface |
| Docker Compose | Runs the optional subjectivity-classifier sidecar |
| `fractalego/subjectivity_classifier` | Dockerized subjectivity/objectivity classifier used by Layer 08 |
| `chreh/persuasive_language_detector` | Persuasive-language detector used in post-processing persuasion checks |
| OpenAI-compatible client libraries | Model-provider access for generation and evaluator-LLM scoring |
| Python standard library / local PNG/SVG helpers | Dependency-light report, plot, and artifact generation |

## Citation Notes

When describing the system in the thesis or an appendix, cite third-party
software and model services according to the citation style used in the paper.
At minimum, cite:

- the subjectivity classifier package;
- Docker or Docker Compose for the sidecar execution environment;
- the persuasive-language detector package;
- any model provider or hosted model used for a reported run;
- any saved final-results JSON dataset used for computational plots.

## Reporting Recommendation

For each reported red-team dataset, record:

- run id;
- date generated;
- selected profiles;
- selected prompt methods;
- target mode, preferably full analysis stack;
- generator model/provider;
- evaluator model/provider;
- whether Docker subjectivity sidecar was active;
- whether any human score overrides were applied;
- analysis artifact folder.
