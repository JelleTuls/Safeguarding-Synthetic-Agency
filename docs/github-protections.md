# GitHub Branch Rules And Repository Protections

This document records the recommended GitHub repository protections for the
public thesis artifact.

## Citation URL Check

The repository remote is:

```text
https://github.com/JelleTuls/Safeguarding-Synthetic-Agency.git
```

The public citation URL in `CITATION.cff` should omit the `.git` suffix:

```text
https://github.com/JelleTuls/Safeguarding-Synthetic-Agency
```

That URL is correct for the current repository remote.

## Recommended Main Branch Ruleset

Create a repository branch ruleset named:

```text
Protect main thesis artifact
```

Target:

```text
main
```

Enforcement:

```text
Active
```

Recommended rules:

| Rule | Recommended Setting | Reason |
| --- | --- | --- |
| Restrict deletions | Enabled | Prevents accidental deletion of `main`. |
| Block force pushes | Enabled | Preserves public release history. |
| Require a pull request before merging | Enabled | Keeps public changes reviewable. |
| Required approvals | 1 | Enough for a single-maintainer thesis artifact. |
| Dismiss stale pull request approvals | Enabled | Forces re-review after meaningful changes. |
| Require review from Code Owners | Enabled | Uses `.github/CODEOWNERS`. |
| Require status checks to pass | Enabled | Blocks merges when the smoke check fails. |
| Required status check | `smoke-check` | Uses `.github/workflows/smoke-check.yml`. |
| Require branches to be up to date before merging | Enabled | Avoids merging stale PR results. |
| Require conversation resolution | Enabled | Prevents unresolved review threads. |
| Require linear history | Enabled | Keeps the thesis artifact history readable. |
| Require signed commits | Optional | Good for provenance, but only enable if you already sign commits. |
| Allow bypass for repository administrators | Disabled after release | Strongest protection once the final artifact is public. |

## Recommended Dev Branch Ruleset

Create a lighter ruleset named:

```text
Protect dev working branch
```

Target:

```text
dev
```

Recommended rules:

| Rule | Recommended Setting |
| --- | --- |
| Restrict deletions | Enabled |
| Block force pushes | Enabled |
| Require status checks to pass | Enabled |
| Required status check | `smoke-check` |
| Require a pull request before merging | Optional |

For a single-person repository, it is fine to push directly to `dev` while using
pull requests for `dev` -> `main`.

## Repository Security Settings

In GitHub, open **Settings -> Code security and analysis** and enable:

- Secret scanning
- Push protection for secrets
- Dependabot alerts
- Dependabot security updates

These settings complement `.gitignore`, `SECURITY.md`, and the local secret
checks described in the README.

## Merge Settings

In **Settings -> General -> Pull Requests**, recommended options are:

- Allow squash merging: enabled
- Allow merge commits: disabled
- Allow rebase merging: optional
- Automatically delete head branches: enabled
- Always suggest updating pull request branches: enabled

Squash merges keep `main` clean while still allowing development history on
feature branches.

## Release Recommendation

After the final public commit is merged to `main`, create a release/tag:

```text
v1.0-thesis-artifact
```

The release should point to the commit that contains the retained final dataset,
analysis artifacts, `CITATION.cff`, `LICENSE`, and public documentation.
