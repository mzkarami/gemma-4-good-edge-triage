# Data Flow

Status: current implementation plus public/private boundary rules.

## Static public demo

```text
site/data.json + public media
  -> static browser UI
  -> label / priority / next action / explanation
```

No model call is required for the curated path.

## Live Gemma preview

```text
browser upload + optional note
  -> HTTPS reverse proxy
  -> localhost-bound live_api.py container/service
  -> upload guardrails and image sanitization
  -> optional local model inference
  -> bounded JSON response
  -> temp upload deletion
```

The Live API should not retain uploaded files or expose raw model traces.

## Field CLI

```text
local report + optional local image/audio path
  -> edge-triage-cli.py
  -> edge_triage_core prompt/config
  -> lazy local model load
  -> constrained triage output
```

Input files remain local to the machine running the CLI.

## Research sandbox

```text
raw shards / cached data / prepared gold set
  -> local_extractor.py / prepare.py
  -> triage_sandbox.py
  -> benchmark predictions
  -> results.tsv
  -> docs/CURRENT_FRONTIER.md when promoted
```

Generated shards, extracted images, and logs should remain ignored unless explicitly sanitized and promoted.
