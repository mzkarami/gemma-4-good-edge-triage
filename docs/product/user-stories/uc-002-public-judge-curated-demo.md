# UC-002: Public Judge Curated Demo

Status: current implementation
Owner surface: `site/`
Primary user: public judge / reviewer
Risk level: public-claims and demo reliability

## Story

As a public judge, I want the demo site to work even if live inference is unavailable, so that I can evaluate the product narrative, metrics, and curated scenarios reliably.

## Current implementation

- `site/` serves curated scenario data from `site/data.json`.
- The curated path does not require model artifacts, GPU, or a hosted API.
- Public metrics are sourced from `../../CURRENT_FRONTIER.md`.

## Acceptance criteria

- Static site loads locally and through Docker.
- Curated path remains usable when Live API is disabled.
- Copy clearly distinguishes curated/offline behavior from live inference.

## Verification

```bash
python3 -m http.server 4173 --directory site
curl -fsS http://127.0.0.1:4173/data.json >/dev/null
```
