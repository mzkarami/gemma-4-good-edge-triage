# Edge-Triage Judge Demo Site

Static judge-facing demo for the Gemma 4 Good Hackathon submission.

## Run locally

Quick local smoke test:

```bash
python3 -m http.server 4173 --directory site
# open http://127.0.0.1:4173
```

Safer public-style container run:

```bash
docker compose up -d --build
# open http://127.0.0.1:4173
```

For public-style deployment guidance, see `../docs/DEPLOYMENT.md` from this directory, or `docs/DEPLOYMENT.md` from the repository root.

## Modes

- **Volunteer Mode:** curated field reports plus two clearly labeled paths:
  - **Curated showcase:** fixed public-safe sample cases from the working product experience. Judges click scenario cards; the UI updates the image, label, priority, next action, and analysis without showing upload controls, calling the model, or sending anything to a server.
  - **Live Gemma preview:** optional guarded API path for judges using the same public site flow, without a pasted token. Images are capped at 25 MB, sanitized server-side, rate-limited, concurrency-limited, timeout-bounded, and sent only when this path is selected.
- **Optimization Mode:** current frontier and EDG-479/EDG-480 ablation decision showing why EDG-480 is the Critical Accuracy Profile candidate.
- **Metrics Source:** `metrics.html` provides a readable metrics page instead of sending judges to raw markdown.

## Design choice

The default judge path is intentionally curated/offline and data-backed. It does not require judges to install models or provide a GPU, and it should not be presented as live inference. The optional Live Gemma preview is separate, guarded by public-demo rate/concurrency/timeout controls, and allowed to fail closed while the curated showcase remains usable.

## Known limitations and safety boundaries

- Edge-Triage is decision support for disaster-response triage, not emergency authority, medical advice, or a replacement for trained incident command.
- Ambiguous or low-context images can be misclassified; responders should verify the scene summary and priority before acting.
- The Live Gemma preview is rate-limited, concurrency-limited, timeout-bounded, and disableable for demo stability, so the curated showcase remains the reliable review path.
- The "Live Gemma 4 vision" scene summary is model-generated and intentionally short; it is meant to explain the classification, not provide operational instructions.

## Data source

Public demo data is in `data.json` and mirrors the competition-facing metrics from `../docs/CURRENT_FRONTIER.md`.
