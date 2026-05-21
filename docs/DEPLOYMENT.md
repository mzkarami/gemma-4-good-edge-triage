# Public Demo Deployment

Target public URL: `https://kaggle.nelly.work/`

This public repository should be deployable without private infrastructure knowledge. The recommended public deployment is a static judge demo plus an optional guarded same-origin Live Gemma preview. Do not expose a full development checkout, `.env` file, model directory, notebook server, raw Python dev server, Docker socket, SSH material, or internal services.

## Recommended architecture

```text
Internet
  -> HTTPS reverse proxy for your demo domain
  -> localhost-bound static demo container
  -> Docker container serving site/ with unprivileged nginx on port 8080
```

The static site is the only required public surface. If the optional Live Gemma preview is enabled, expose it only through the same HTTPS reverse-proxy path (`/api/`) with upload limits, rate limits, daily limits, concurrency controls, timeout controls, and the kill switch available.

The compose file defaults to localhost-only binding:

```yaml
ports:
  - "${DEMO_BIND_ADDRESS:-127.0.0.1}:4173:8080"
```

For public judging, keep the app itself localhost-only and put a public HTTPS reverse proxy in front of it.

## Why Docker is safer than `python3 -m http.server`

Running the quick Python server is fine for local smoke tests, but Docker is the safer public option because:

- the container only contains the static `site/` files, not the full repo or home directory;
- nginx runs as an unprivileged user;
- the compose file drops Linux capabilities;
- the filesystem is read-only;
- `no-new-privileges` is enabled;
- the public reverse proxy can add HTTPS, rate limiting, and security headers;
- a compromise of this static container should not expose model artifacts, API keys, SSH keys, notebooks, or the rest of the host.

Docker is not a perfect security boundary by itself, so still keep the host patched and expose only the HTTPS proxy publicly.

## Run locally in Docker

From the repo root:

```bash
docker compose up -d --build
curl -I http://127.0.0.1:4173/
curl -fsS http://127.0.0.1:4173/data.json >/dev/null
```

Stop it with:

```bash
docker compose down
```

## Optional guarded live inference preview

The Live Gemma preview is intentionally separate from the static site. Judges do not need an account or pasted token for the current public judging flow. The curated offline demo remains available even if this service is stopped.

Local smoke test:

```bash
export DEMO_BIND_ADDRESS=127.0.0.1
export LIVE_API_BIND_ADDRESS=127.0.0.1
export EDGE_TRIAGE_LIVE_MODEL=0   # fallback/smoke mode; set 1 only after model check

docker compose --profile live up -d --build
curl -fsS http://127.0.0.1:4180/healthz
```

Live model mode:

```bash
uv run prepare.py  # ensures the GGUF model and Edge-Triage-mmproj-F16.gguf exist locally
export EDGE_TRIAGE_MODEL_DIR="$HOME/.cache/autoresearch/models"  # or copy/link those files into ./models
export EDGE_TRIAGE_LIVE_MODEL=1
docker compose --profile live up -d --build edge-triage-live-api
```

Security controls applied to the live API:

- token-free public judging flow bounded by server-side guardrails;
- 25 MB upload cap in app and nginx (`client_max_body_size 25m`);
- JPEG/PNG/WebP only;
- image is decoded, EXIF-transposed, metadata-stripped, and re-encoded before inference;
- text notes are sanitized and capped at 1000 characters;
- audio is local-only in the current public app and is not sent to the backend;
- uploaded files live only under `/tmp` and are deleted after the request;
- no URL fetching and no persistent upload storage;
- rate limit defaults: 6 requests/minute and 60/day;
- concurrency cap defaults to 2 public requests, with model lock protection;
- model timeout is bounded by `EDGE_TRIAGE_MODEL_TIMEOUT_SECONDS`;
- kill switch available via `EDGE_TRIAGE_PUBLIC_API_ENABLED=0`;
- no raw model stack traces or raw model output returned to judges;
- container hardening: non-root, read-only filesystem, tmpfs `/tmp`, dropped capabilities, `no-new-privileges`, process/memory limits.

OWASP / OWASP AI-aligned controls without making judging painful:

- **A01 Broken Access Control:** intentionally public API path with bounded resource controls; static site remains public.
- **A02 Cryptographic Failures:** expose publicly only through HTTPS reverse proxy; do not log upload contents or secrets.
- **A03 Injection / LLM prompt injection:** uploaded notes are treated as untrusted scene descriptions, length-capped to 1000 characters, control characters stripped, and inserted only into a fixed classifier prompt. The model is not given tools, shell access, network access, or filesystem write capabilities.
- **A04 Insecure Design:** live API is separate from the static site and can fail closed without breaking the demo.
- **A05 Security Misconfiguration:** default bindings are localhost/private; raw Uvicorn is never public.
- **A06 Vulnerable Components:** dependency changes are locked in `uv.lock`; rebuild before final sharing.
- **A07 Identification/Auth Failures:** no account creation and no pasted frontend token; constrain access through public demo guardrails instead of weak client-side secrets.
- **A08 Integrity Failures:** accepted image formats are decoded/re-encoded; arbitrary files are rejected.
- **A09 Logging/Monitoring:** log request status/latency only; do not store uploaded images or field notes in public logs.
- **A10 SSRF:** API never fetches remote URLs.
- **OWASP Top 10 for LLM/AI:** prompt injection is contained by fixed output labels and no tools; sensitive info disclosure is reduced by no secrets in prompts/responses; model DoS is mitigated with size/rate/time/inflight limits; insecure plugin/tool use is avoided because the model has no plugins.

## Caddy reverse proxy

If Caddy is already installed on the host, adapt `deploy/Caddyfile.example` for your domain.

Example:

```caddyfile
your-demo-domain.example {
    encode zstd gzip
    reverse_proxy 127.0.0.1:4173
}
```

Then reload Caddy after pointing DNS at the server.

## Nginx reverse proxy alternative

If the host uses system nginx instead of Caddy:

```nginx
server {
    listen 80;
    server_name your-demo-domain.example;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-demo-domain.example;

    # Configure certificates with certbot or existing TLS automation.

    location / {
        proxy_pass http://127.0.0.1:4173;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Pre-public checklist

Before sharing the public URL:

1. DNS for your demo domain points to the intended host.
2. `docker compose ps` shows the demo container as healthy or running.
3. `curl -I https://your-demo-domain.example/` returns `200` and HTTPS headers.
4. `curl -fsS https://your-demo-domain.example/data.json >/dev/null` succeeds.
5. `ss -tulpn` shows only the reverse proxy public on 80/443; the demo app remains localhost-only on `127.0.0.1:4173`.
6. No live model API, notebook server, SSH key material, `.env`, or full repo directory is served publicly unless the guarded live API was intentionally enabled behind HTTPS and public-demo controls.
7. If Live Gemma preview is enabled, verify over-25 MB uploads fail, malformed/corrupt images fail, rate/concurrency controls work, and the token-free public path succeeds.

## Demo modes

The static app supports both judge modes:

- Volunteer Mode: curated field reports, triage label, priority, latency, explanation, and conservative next action. Its curated offline path uses fixed public-safe samples; its Live Gemma preview path calls the guarded API only when selected.
- Optimization Mode: current frontier cards plus EDG-478/EDG-479/EDG-480 ablation evidence. Critical Accuracy is presented here as a validated profile, not as a third top-level UI mode.

The page includes an explicit mode switcher so judges can toggle between both experiences without relying only on scrolling/navigation links.
