# Edge-Triage Testing Strategy

## Docs-only changes

Run:

```bash
python3 scripts/check_docs_links.py
```

Also run `git diff --check` before committing.

## Code/runtime changes

Run the CI-safe local suite first:

```bash
uv run python scripts/run_ci_tests.py
uv run python edge-triage-cli.py --help
uv run python triage_sandbox.py --help
```

For prompt routing, sandbox, benchmark, or native-runtime changes, run the full maintainer suite:

```bash
uv run python scripts/run_full_local_tests.py
```

That script enables `EDGE_TRIAGE_RUN_NATIVE_TESTS=1` for sandbox tests that import native llama.cpp/torch runtime modules.

## Live API changes

Run the Live API unit tests and the optional full-stack smoke when relevant:

```bash
uv run python -m unittest tests.test_live_api tests.test_live_api_security_controls -v
EDGE_TRIAGE_RUN_E2E=1 scripts/e2e_smoke.sh
```

## Benchmark/frontier changes

Run a comparable benchmark before updating public claims. Update `results.tsv`, `docs/CURRENT_FRONTIER.md`, and a validation report together.

## CI expectation

GitHub Actions should run `uv run python scripts/run_ci_tests.py`, CLI help, and sandbox help for every push/PR. Full sandbox-heavy test discovery remains a local/pre-merge maintainer check because some hosted runners can terminate native model/runtime paths with CPU-instruction errors unrelated to the docs/code change.
