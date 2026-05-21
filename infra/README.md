# Optional Paperclip Infrastructure

This directory contains a public-safe example for running a local Paperclip-style research hub around Edge-Triage.

It is optional. You do not need it for:

- the public static demo;
- the field CLI;
- the benchmark harness;
- Kaggle judging.

Use it only if you want a local dashboard/control plane for the autonomous research loop.

## Start locally

```bash
export PAPERCLIP_DB_PASSWORD="$(openssl rand -base64 32)"
docker compose -f infra/docker-compose.paperclip.example.yml up -d
```

Then open:

```text
http://127.0.0.1:3100
```

## Safety notes

- The example binds services to `127.0.0.1` by default.
- Do not expose this stack directly to the public internet.
- Do not commit `.env` files, database volumes, generated logs, uploaded images, or disaster reports.
- Use proper authentication, TLS, and network policy before any shared deployment.
