# Live API Security Boundary

Status: current implementation.

The Live Gemma preview is optional and public-demo bounded. It exists to show live behavior without making the curated demo depend on a model server.

## Required controls

- Same-origin reverse proxy; raw API port should remain localhost/private.
- Upload size cap.
- JPEG/PNG/WebP allow-list.
- Decode, EXIF-transpose, metadata-strip, and re-encode uploaded images.
- Note text sanitization and length cap.
- No remote URL fetching.
- No persistent upload storage.
- Rate and daily limits.
- Public concurrency cap plus model lock.
- Model timeout.
- Kill switch through environment config.
- No raw stack traces or secrets in responses.
- Container hardening where Docker is used.

## Failure behavior

The Live API should fail closed with a safe message. The static curated demo must remain available.

## Verification

```bash
uv run python -m unittest tests.test_live_api tests.test_live_api_security_controls -v
EDGE_TRIAGE_RUN_E2E=1 scripts/e2e_smoke.sh
```
