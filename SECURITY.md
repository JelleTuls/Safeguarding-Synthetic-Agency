# Security Policy

## Research Prototype Scope

This repository is a public research artifact for a thesis project. It is not a
production safety product, hosted service, compliance system, or audited
security control. The code is intended for local review, demonstration,
red-teaming experiments, and reproducible analysis of the included reference
dataset.

## Reporting Issues

If you find a security-sensitive issue after this repository is published,
please report it privately through the hosting platform's private security
advisory feature when available. Do not paste API keys, private prompts,
personal data, or exploit details into a public issue.

Examples of security-sensitive reports include:

- accidentally committed secrets or credentials;
- prompt/data leakage in saved reports;
- unsafe local file exposure through an API route;
- dependency vulnerabilities that affect local execution;
- redaction failures in logs or exported artifacts.

## Secrets

Do not commit real `.env` files, API keys, provider endpoints containing
credentials, access tokens, local logs, or private run outputs. The project uses
copy-ready `.env.example` files so users can create local `.env` files without
placing secrets in git.

If a real secret is ever committed, rotate the credential immediately. Removing
the current file is not enough if the secret exists in git history.

## Supported Version

The thesis-facing public artifact is the tagged release intended to match the
final reference dataset and analysis outputs. Later local experiments may change
behavior and should be treated as development work unless a new release says
otherwise.
