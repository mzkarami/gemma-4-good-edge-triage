# Test Strategy

Status: current testing contract.

## Test layers

1. **Docs checks:** local markdown links and whitespace checks.
2. **Core/import-boundary tests:** prove shared contracts remain side-effect free.
3. **API guardrail tests:** prove upload, sanitization, fallback, and safe error behavior.
4. **Sandbox tests:** prove research-loop invariants, state hashing, and benchmark guardrails.
5. **Optional e2e smoke:** static site plus guarded Live API fallback path.

## Required commands by change type

### Docs-only

```bash
python3 scripts/check_docs_links.py
git diff --check
```

### CI-safe local check

```bash
uv run python scripts/run_ci_tests.py
uv run python edge-triage-cli.py --help
uv run python triage_sandbox.py --help
```

This matches the GitHub Actions validation path and avoids importing native model runtimes during unit-test discovery.

### Full local maintainer check

```bash
uv run python scripts/run_full_local_tests.py
```

`run_full_local_tests.py` sets `EDGE_TRIAGE_RUN_NATIVE_TESTS=1` for the subprocess so sandbox tests that import `llama_cpp`/`torch` run only on a maintainer machine. If the native runtime is unavailable or unsupported, use the CI-safe check and document the limitation.

### Shared core / CLI / sandbox

```bash
uv run python scripts/run_full_local_tests.py
```

### Live API

```bash
uv run python -m unittest tests.test_live_api tests.test_live_api_security_controls -v
```

### Public demo

```bash
python3 -m http.server 4173 --directory site
curl -fsS http://127.0.0.1:4173/data.json >/dev/null
```

### Optional full-stack

```bash
EDGE_TRIAGE_RUN_E2E=1 scripts/e2e_smoke.sh
```
