# Edge-Triage Media Library

This directory contains public-safe media assets for the Kaggle submission, media gallery, and 3-minute video.

## Assets

| Asset | Purpose |
| --- | --- |
| `brand/edge-triage-logo-square.png` | Square logo cropped from the selected Unsplash center-circle image. |
| `brand/edge-triage-logo-icon.png` | Round transparent logo for the site header, hero, and favicon treatment. |
| `brand/edge-triage-cover-1600x900.jpg` | Kaggle/media-gallery cover image with project title and canonical metrics. |
| `brand/edge-triage-cover-1200x675.jpg` | README/social cover variant. |
| `screenshots/01-landing-hero.png` | Opening/cover shot showing the product framing and frontier metrics. |
| `screenshots/02-volunteer-mode.png` | Field-facing triage workflow for the demo walkthrough. |
| `screenshots/03-optimization-mode.png` | Autonomous research cockpit and EDG-480 frontier evidence. |
| `screenshots/04-metrics-page.png` | Validated Speed/Accuracy profile metrics for evidence slides. |
| `screenshots/05-live-result-card.png` | Close-up of the polished live Gemma 4 vision result card. |
| `screenshots/06-live-optimization-bridge-flood.png` | Optimization Mode live Gemma result for a real flood-damaged bridge photo. |
| `screenshots/07-live-optimization-relief-supplies.png` | Optimization Mode live Gemma result for a real relief-supplies photo. |
| `screenshots/08-live-optimization-evacuation-assistance.png` | Optimization Mode live Gemma result for a real evacuation-assistance photo. |
| `scenario-inputs/*.jpg` | Public-domain source photos used for curated examples and live scenario captures. |
| `live-results/*.json` | Public-safe live API outputs used to render the corresponding screenshots. |
| `charts/research-progress.png` | Research progress chart copied from the root `progress.png`. |

## Regenerate

```bash
python3 scripts/capture_media_assets.py
```

The capture script starts a temporary local server for `site/` and uses Chromium/Chrome in headless mode.

## Public-safety rule

These assets are intended to be public. Do not add judge tokens, `.env` values, private IP-only URLs, credentials, raw uploads, or private Kaggle notes here.

See `ASSET_CREDITS.md` for source and license credits.
