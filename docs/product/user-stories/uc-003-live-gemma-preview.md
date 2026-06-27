# UC-003: Optional Live Gemma Preview

Status: current implementation
Owner surface: `live_api.py`, Docker live profile
Primary user: public judge / live demo operator
Risk level: upload/security/resource-control

## Story

As a demo operator, I want the Live API to share labels/prompts with the CLI while keeping HTTP guardrails local, so that the public endpoint is consistent but still hardened for uploads.

## Current implementation

- `live_api.py` imports shared label, prompt, config, and result helpers from `edge_triage_core/`.
- Upload size, MIME validation, image sanitization, rate/day limits, concurrency cap, timeout, and kill switch remain in `live_api.py`.

## Acceptance criteria

- API returns bounded JSON without raw model traces.
- Uploaded files are temporary and deleted after the request.
- Corrupt, oversized, or unsupported uploads fail safely.
- Curated demo remains usable when live model mode is disabled.

## Verification

```bash
uv run python -m unittest tests.test_live_api tests.test_live_api_security_controls -v
```
