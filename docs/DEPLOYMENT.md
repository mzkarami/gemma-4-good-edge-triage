# Public Demo Deployment

Target public URL: `https://kaggle.nelly.work/`

Before exposing anything publicly, read [`PUBLIC_DEMO_SECURITY_PLAN.md`](PUBLIC_DEMO_SECURITY_PLAN.md). The current target is a static judge demo plus a guarded same-origin Live Gemma preview: no full repo, `.env`, model directories, notebooks, raw Python dev servers, Docker socket, or internal services exposed. If deploying from `dev@100.97.113.99`, follow the handoff section in that plan before making changes.

The judge-facing demo is static and data-backed, so the safest public deployment is a small read-only container behind an HTTPS reverse proxy. This avoids exposing the development checkout, Python process, model files, or any local credentials to the public internet.

An optional live inference preview now exists for judges who want to upload an image and exercise the Gemma path. It is a separate guarded API service, disabled by default, and should be exposed only with rate limits, daily limits, concurrency controls, a kill switch, a 25 MB upload cap, and reverse-proxy controls.

## Recommended architecture for Kaggle judges

```text
Internet
  -> HTTPS reverse proxy on kaggle.nelly.work
  -> 127.0.0.1:4173 on the host
  -> Docker container serving site/ with unprivileged nginx on port 8080
```

The static site is the only required public surface. If the optional Live Gemma preview is enabled, expose it only through the same HTTPS reverse proxy path (`/api/`) with upload limits, rate limits, daily limits, concurrency controls, timeout controls, and the kill switch available. Do not expose the Python demo server, raw Uvicorn port, notebooks, databases, SSH keys, `.env` files, model files, or the full repository. The compose file defaults to localhost-only binding:

```yaml
ports:
  - "${DEMO_BIND_ADDRESS:-127.0.0.1}:4173:8080"
```

For private tailnet testing, start it with the host's Tailscale IP:

```bash
DEMO_BIND_ADDRESS=$(tailscale ip -4) docker compose up -d --build
```

Then open `http://experiment:4173/` or `http://100.76.13.15:4173/` from a laptop on the same tailnet.

For public judging, keep the app itself localhost-only and put the public HTTPS reverse proxy in front of it.

## Tailscale-only preview vs public Kaggle URL

Tailscale does not automatically make `https://kaggle.nelly.work/` private. Access depends on how DNS and the reverse proxy are configured:

- **Tailnet-only preview:** expose the site with Tailscale Serve or bind the reverse proxy only to the Tailscale IP, for example `100.76.13.15`. Only devices/users in the tailnet can reach it.
- **Public Kaggle submission:** point public DNS for `kaggle.nelly.work` at the host and let Caddy/Nginx listen publicly on 80/443. Anyone with the URL can reach the static site, including judges.
- **Do not use Tailscale Funnel unless intended:** Funnel is public internet exposure through Tailscale, not tailnet-only access.

For final judging, use the public Kaggle URL but serve only the static Dockerized site. For private review before submission, use a Tailscale-only URL.

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

Private tailnet smoke test:

```bash
export DEMO_BIND_ADDRESS=$(tailscale ip -4)
export LIVE_API_BIND_ADDRESS=$(tailscale ip -4)
export EDGE_TRIAGE_LIVE_MODEL=0   # fallback/smoke mode; set 1 only after model check

docker compose --profile live up -d --build
curl -fsS http://100.76.13.15:4180/healthz
```

Live model mode:

```bash
uv run prepare.py  # ensures the GGUF model and Edge-Triage-mmproj-F16.gguf are in ~/.cache/autoresearch/models
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

If Caddy is already installed on the host, adapt `deploy/Caddyfile.example`:

```caddyfile
kaggle.nelly.work {
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
    server_name kaggle.nelly.work;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name kaggle.nelly.work;

    # Configure certificates with certbot or the existing host TLS automation.

    location / {
        proxy_pass http://127.0.0.1:4173;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Pre-public checklist

Before sharing the Kaggle URL:

1. DNS for `kaggle.nelly.work` points to the intended host.
2. `docker compose ps` shows the demo container as healthy or running.
3. `curl -I https://kaggle.nelly.work/` returns `200` and HTTPS headers.
4. `curl -fsS https://kaggle.nelly.work/data.json >/dev/null` succeeds.
5. `ss -tulpn` shows only the reverse proxy public on 80/443; the demo app remains localhost-only on 127.0.0.1:4173.
6. No live model API, notebook server, SSH key material, `.env`, or full repo directory is served publicly unless the guarded live API was intentionally enabled behind HTTPS and public-demo controls.
7. If Live Gemma preview is enabled, verify over-25 MB uploads fail, malformed/corrupt images fail, rate/concurrency controls work, and the token-free public path succeeds.

## Demo modes

The static app supports both judge modes:

- Volunteer Mode: curated field reports, triage label, priority, latency, explanation, and conservative next action. Its curated offline path uses fixed public-safe samples; its Live Gemma preview path calls the guarded API only when selected.
- Optimization Mode: current frontier cards plus EDG-478/EDG-479/EDG-480 ablation evidence. Critical Accuracy is presented here as a validated profile, not as a third top-level UI mode.

The page now includes an explicit mode switcher so judges can toggle between both experiences without relying only on scrolling/navigation links.
