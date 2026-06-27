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

### Shared core / CLI / sandbox

```bash
uv run python -m unittest discover tests/
uv run python edge-triage-cli.py --help
uv run python triage_sandbox.py --help
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
