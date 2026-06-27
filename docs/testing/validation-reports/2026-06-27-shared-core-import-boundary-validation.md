# Shared Core Import-Boundary Validation

Date: 2026-06-27
Commit: `be895c4` public, `51f31c7` private
Change: extracted shared prompt, label, config, and result contracts into `edge_triage_core/` and updated CLI, Live API, and sandbox consumers.

## Commands run

```bash
uv run python -m unittest discover tests/
uv run python edge-triage-cli.py --help
uv run python triage_sandbox.py --help
```

## Results

- Unit suite passed locally in both public and private repos.
- CLI help smoke passed.
- Sandbox help smoke passed.
- Import-boundary tests were added for core and CLI startup.

## GitHub Actions

- Public repo CI passed after `295f48c`.
- Private repo workflow passed after `72ccd00`; optional SSH deploy path was skipped when deployment secrets were absent.

## Risks

- Public repo has local untracked `.idea/` metadata that should remain uncommitted.
- Future prompt changes must account for CLI, Live API, and sandbox consumers.

## Follow-up

- Keep ADR-001 and runtime-boundary docs aligned with future core changes.
- Add docs-link checks to CI.
