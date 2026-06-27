# DevOps and Deployment

## 1. Public surface should be minimal

Expose the static demo through HTTPS. Keep raw app/API ports localhost-only unless intentionally reverse-proxied with guardrails.

## 2. Live API is optional and fail-closed

The curated offline demo must remain usable even if live inference is disabled, unavailable, rate-limited, or missing model artifacts.

## 3. Do not weaken Compose defaults for convenience

Default bindings should remain localhost/private. Any public exposure should happen through an explicit HTTPS reverse proxy.

## 4. Deployment claims require read-back

After push or deploy, verify remote branch head, GitHub Actions status, and public URL smoke output before claiming success.

## 5. Private operator details stay private

Private hostnames, Tailscale routes, Caddy specifics, server paths, and secrets should live in private/operator docs, not the public repo.
