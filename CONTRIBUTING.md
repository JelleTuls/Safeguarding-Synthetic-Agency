# Contributing

Thank you for taking the time to inspect or improve this thesis artifact. The
repository is primarily maintained as the applied companion codebase for the
research project, so changes should preserve reproducibility and avoid
unintended shifts in the saved reference dataset.

## Local Setup

Use the project scripts from the repository root:

```bash
bash scripts/prepare_project.sh
./start.sh
```

Run the smoke check before opening a pull request:

```bash
bash scripts/smoke_check.sh
```

## Development Principles

- Keep the lightweight baseline and guardrailed pipeline clearly separated.
- Do not hardcode scoring outcomes to make the guardrailed system look better.
- Keep red-team scoring logic reproducible and explainable.
- Preserve the curated reference dataset unless intentionally preparing a new
  public release.
- Add or update documentation when behavior changes.
- Keep `.env`, logs, local runs, and private generated artifacts out of git.

## Data And Reports

The repository intentionally keeps one thesis-facing final report and its
generated computational-analysis artifacts. New runtime outputs are local by
default and should only be committed when they are intentionally curated,
sanitized, and documented.

Before committing new reports or plots, check:

- the run id is referenced from the README or reference-dataset document;
- JSON/PDF artifacts contain no secrets or private data;
- generated analysis artifacts match the saved JSON report;
- skipped plots or warnings are documented honestly.

## Commit Checklist

Before publishing changes:

```bash
bash scripts/smoke_check.sh
git status --short
```

Also run a secret scan with your preferred tool before making the repository or
release public.
