# Feature Slice Validation: Action Packs, Red Flags, Queue, and Radio Scripts

Date: 2026-06-27
Status: current validation report

## Change

Added four product features from internal product review and field-workflow design:

- Responder Action Pack in shared response shaping.
- Deterministic red-flag escalation.
- Local incident queue/export in the volunteer console and CLI JSONL save.
- Scoped English/Spanish radio-script text mode.

## Files of interest

- `edge_triage_core/actions.py`
- `edge_triage_core/safety.py`
- `edge_triage_core/language.py`
- `edge_triage_core/results.py`
- `edge-triage-cli.py`
- `live_api.py`
- `site/app.html`
- `site/app.js`
- `site/data.json`

## Verification

Run before promotion:

```bash
python3 scripts/check_docs_links.py
git diff --check
uv run python scripts/run_ci_tests.py
uv run python edge-triage-cli.py --help
uv run python triage_sandbox.py --help
```

For native/sandbox changes, also run:

```bash
uv run python scripts/run_full_local_tests.py
```

## Risks

- Radio script mode is text-only; do not claim evaluated multilingual/dialect/TTS support.
- Incident queue/export is local-only; no automatic sync or notifications are implemented.
- Red-flag escalation is conservative and keyword-based; it supports human review, not emergency authority.
