# Edge-Triage Architecture

Edge-Triage has two user-facing paths and one measurement loop.

```text
Volunteer / responder
  -> static web UI or CLI
  -> Gemma 4 triage profile
  -> label, priority, confidence context, conservative next action

Research / response lead
  -> triage_sandbox.py
  -> gold-set evaluation
  -> results.tsv
  -> docs/CURRENT_FRONTIER.md
```

## Components

- `site/`: static public demo with volunteer and optimization views. The static mode uses curated public-safe scenarios so it works without a hosted model.
- `live_api.py`: optional FastAPI service for a guarded Live Gemma preview. It requires a judge token, upload limits, rate limits, MIME validation, and same-origin/reverse-proxy deployment.
- `edge-triage-cli.py`: local field CLI for text/image-style disaster reports.
- `triage_sandbox.py`: repeatable evaluation harness for label quality, latency, routing mix, and keep/discard decisions.
- `results.tsv`: experiment ledger.
- `docs/CURRENT_FRONTIER.md`: public source of truth for current benchmark claims.
- `litert_backend.py` and `Modelfile`: deployment scaffolds for LiteRT/Google AI Edge and local model runners.

## Safety model

Edge-Triage is a triage assistant, not an incident commander or medical authority. It uses constrained categories, conservative next actions, human-readable evidence, and local-first deployment assumptions so responders keep control.

## Deployment model

For public judging, serve the static site over HTTPS and keep raw app/API ports private. If the optional live API is enabled, expose it only through the HTTPS origin under `/api/*`, require the judge token, and keep the model directory mounted read-only.
