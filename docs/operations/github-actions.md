# GitHub Actions

Status: current CI overview.

## Public repo

Workflow: `Edge-Triage CI`

Runs:

- dependency sync with `uv`;
- `uv run python scripts/run_ci_tests.py`;
- CLI help smoke;
- sandbox help smoke;

## Private repo

Workflow: `Edge-Triage CI/CD (Field Hub)`

Runs validation first. Manual deploy is optional and gated on deployment secrets. If secrets are absent, validation can still succeed and SSH deploy is skipped.

## Verification after push

```bash
gh run list --limit 5
gh run watch <run-id> --exit-status
gh run view <run-id> --json status,conclusion,jobs,url
```
