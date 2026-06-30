# Public and Private Documentation Boundary

Status: current operating rule.

## Evaluation-window stability

The submission package is closed, but judges may still evaluate submitted public links. During this window, keep public URLs, submitted-package reference docs, and `docs/CURRENT_FRONTIER.md` stable and non-contradictory while continuing additive project improvements.

## Public repository may include

- Product and architecture docs.
- Sanitized deployment patterns.
- Public benchmark claims and research logs.
- CI and local verification commands.
- Generic reverse-proxy and Docker guidance.
- Evaluation-window stability notes that do not expose private infrastructure.

## Public repository must not include

- Private server hostnames or IPs.
- Tailscale-only operational details.
- `.env` files, secrets, SSH material, API keys, or Kaggle credentials.
- Raw sensitive disaster data.
- Private notes or local-only operator incidents.
- Model weights or generated local caches.

## Private repository may include

- Actual operator runbooks.
- Server-specific deployment details.
- Private artifact locations.
- Operational incident notes.

When in doubt, keep public docs generic and put specific operator reality in the private repo.
