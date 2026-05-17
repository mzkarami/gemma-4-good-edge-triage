# Deployment Guide

This repo supports two deployment modes.

## 1. Static judge demo

The safest public path is the static site in `site/`.

```bash
docker compose up -d --build edge-triage-demo
curl -I http://127.0.0.1:4173/
curl -fsS http://127.0.0.1:4173/data.json >/dev/null
```

For production, put Caddy, nginx, or a managed static host in front of the container and expose only HTTPS.

## 2. Optional guarded Live Gemma preview

The live API is optional. It should fail closed until a real token and model artifacts are configured.

```bash
cp .env.example .env
# edit .env with the judge token, allowed origin, and model directory
docker compose --profile live up -d --build edge-triage-live-api
curl -fsS http://127.0.0.1:4180/healthz
```

Security expectations:

- keep raw ports bound to localhost or a private interface;
- expose public traffic only through HTTPS;
- route `/api/*` to the live API only when token auth is configured;
- require `X-Judge-Token` or `Authorization: Bearer ...`;
- keep model artifacts outside git and mount them read-only;
- limit uploads and request rate.

See `deploy/Caddyfile.example` for a same-origin reverse proxy shape.
