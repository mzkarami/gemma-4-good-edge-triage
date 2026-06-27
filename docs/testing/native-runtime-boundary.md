# Native Runtime Test Boundary

Status: current testing guardrail.

## Why this exists

A previous public GitHub-hosted runner failed with exit code `132` while full `unittest discover` imported native model/runtime paths. Exit code `132` usually indicates `SIGILL` / illegal CPU instruction. The failure happened after llama.cpp/model/data bootstrap logs, not as a normal Python assertion failure.

## Policy

- GitHub Actions runs `scripts/run_ci_tests.py`, CLI help, and sandbox help.
- Sandbox-heavy tests that import `llama_cpp`/`torch` require `EDGE_TRIAGE_RUN_NATIVE_TESTS=1`.
- Maintainers run `scripts/run_full_local_tests.py` before benchmark, prompt-routing, model-runtime, or frontier changes.
- If native runtime is unavailable locally, report that limitation and provide CI-safe validation instead of claiming full native coverage.

## Commands

CI-safe:

```bash
uv run python scripts/run_ci_tests.py
uv run python edge-triage-cli.py --help
uv run python triage_sandbox.py --help
```

Full local:

```bash
uv run python scripts/run_full_local_tests.py
```

Manual native sandbox module run:

```bash
EDGE_TRIAGE_RUN_NATIVE_TESTS=1 uv run python -m unittest tests.test_triage_sandbox -v
```
