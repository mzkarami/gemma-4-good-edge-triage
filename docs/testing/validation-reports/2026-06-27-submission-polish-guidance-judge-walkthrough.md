# Submission Polish Validation: Guidance Basis and Judge Walkthrough

Date: 2026-06-27
Status: current validation report

## Change

Added a deterministic guidance-basis response field, public disaster-response guidance pack, judge walkthrough page, and volunteer-console UX polish for action packs, red flags, guidance basis, local queue/export, and radio handoff review.

## Verification

Run before promotion:

```bash
python3 scripts/check_docs_links.py
git diff --check
uv run python scripts/run_ci_tests.py
uv run python edge-triage-cli.py --help
uv run python triage_sandbox.py --help
```

Run full local native validation when changing model/runtime behavior:

```bash
uv run python scripts/run_full_local_tests.py
```

## Public-safety checks

Search for external-submission references before commit. No public docs/code should mention other projects or source writeups as feature rationale.

## Risks

- Guidance snippets are conservative support text only.
- Judge walkthrough is explanatory; it does not add automatic dispatch, sync, diagnosis, or incident-command authority.
