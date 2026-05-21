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
- `agents/`: optional templates for Paperclip-style NGO/research workspaces that want an agentic loop around the benchmark.
- `plugin/`: optional local Paperclip dashboard skeleton that reads `results.tsv`.
- `infra/`: optional public-safe local Paperclip compose example.
- `data/` and `logs/`: local workspace placeholders; generated shards, images, and logs stay out of git.
- `litert_backend.py` and `Modelfile`: deployment scaffolds for LiteRT/Google AI Edge and local model runners.

## Agentic research loop

The optimization side is inspired by Andrej Karpathy's AutoResearch-style pattern: define a fixed harness, give an agent a narrow sandbox to edit, and apply a measured keep/discard rule. Edge-Triage adapts that idea for humanitarian triage:

- the editable sandbox is `triage_sandbox.py`;
- the fixed benchmark and data preparation live in `prepare.py` and the gold-set path;
- the experiment ledger is `results.tsv`;
- the optional agent templates live in `agents/`;
- human review is required before agent-discovered changes become deployment defaults.

## Safety model

Edge-Triage is a triage assistant, not an incident commander or medical authority. It uses constrained categories, conservative next actions, human-readable evidence, and local-first deployment assumptions so responders keep control.

## Deployment model

For public judging, serve the static site over HTTPS and keep raw app/API ports private. If the optional live API is enabled, expose it only through the HTTPS origin under `/api/*`, require the judge token, and keep the model directory mounted read-only.
