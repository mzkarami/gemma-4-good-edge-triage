# Edge-Triage Documentation Map

Status: canonical documentation entry point.

This directory is the home for Edge-Triage product, architecture, research, testing, operations, submission, and reference documentation. Use `instructions/` for the team/agent operating layer. Use `docs/` for product and system knowledge.

## Start here

- [Product](product/README.md) - product brief, roadmap, public claims guidance, and user stories.
- [Architecture](architecture/README.md) - current architecture, runtime boundaries, data flow, live API boundary, research loop, diagrams, and ADRs.
- [Testing and evaluation](testing/README.md) - test strategy, validation reports, CI, and benchmark evidence.
- [Operations](operations/README.md) - deployment, public demo checklist, live API runbook, GitHub Actions, and local field operations.
- [Research](research/README.md) - current frontier, experiment methodology, ledger rules, and EDG research logs.
- [Submission](submission/README.md) - Kaggle-facing writeups, video script, and public submission materials.
- [Reference](reference/README.md) - historical or compatibility material that should not override current docs.

## Canonical sources for current work

- `instructions/` for project principles, safety/privacy rules, architecture rules, testing strategy, and agent workflow.
- `docs/CURRENT_FRONTIER.md` for public benchmark claims until the research docs migration is complete.
- `docs/architecture/` for current runtime boundaries and decisions.
- `docs/testing/` for validation evidence and verification expectations.
- `docs/operations/` and `docs/DEPLOYMENT.md` for deployment and public-demo operations until the operations migration is complete.

## Current vs target vs reference

Every durable doc should make clear whether it describes:

- **Current:** implemented and verified in this repository, backed by tests, CI, `results.tsv`, `docs/CURRENT_FRONTIER.md`, or live smoke output.
- **Target/future:** desired direction that requires implementation and validation before it becomes a public claim.
- **Reference/historical:** useful context, older research, or compatibility material that does not override current architecture, frontier, or safety docs.

## Rule of precedence

When documents disagree:

1. User/founder instruction for the current task wins.
2. Safety, privacy, and security requirements win over convenience.
3. `instructions/`, this file, and `docs/architecture/` define current project rules.
4. `docs/CURRENT_FRONTIER.md` defines public benchmark claims.
5. `docs/testing/` defines validation evidence.
6. `docs/reference/`, `docs/superpowers/research_logs/`, and older submission drafts are historical/reference unless promoted by a current doc.

## Public vs private boundary

The public repository should contain sanitized product, architecture, research, and deployment-pattern documentation. It must not contain private server details, secrets, Tailscale-only hostnames, private notes, raw sensitive disaster data, `.env` files, model credentials, or SSH material.

Private/operator docs may describe the actual deployment environment, but public docs should describe safe patterns rather than private infrastructure reality.
