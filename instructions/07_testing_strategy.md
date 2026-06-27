# Edge-Triage Testing Strategy

## Docs-only changes

Run:

```bash
python3 scripts/check_docs_links.py
```

Also run `git diff --check` before committing.

## Code/runtime changes

Run:

```bash
uv run python -m unittest discover tests/
uv run python edge-triage-cli.py --help
uv run python triage_sandbox.py --help
```

## Live API changes

Run the Live API unit tests and the optional full-stack smoke when relevant:

```bash
uv run python -m unittest tests.test_live_api tests.test_live_api_security_controls -v
EDGE_TRIAGE_RUN_E2E=1 scripts/e2e_smoke.sh
```

## Benchmark/frontier changes

Run a comparable benchmark before updating public claims. Update `results.tsv`, `docs/CURRENT_FRONTIER.md`, and a validation report together.

## CI expectation

GitHub Actions should run unit tests, CLI help, sandbox help, and docs-link checks for every push/PR.
