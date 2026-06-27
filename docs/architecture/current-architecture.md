# Current Architecture

Status: current implementation.

Edge-Triage has two user-facing paths and one measurement loop.

```text
Volunteer / responder
  -> static web UI or CLI
  -> edge_triage_core shared prompt/label/runtime contract
  -> Gemma 4 triage profile or curated fallback data
  -> label, priority, confidence context, conservative next action

Research / response lead
  -> triage_sandbox.py
  -> edge_triage_core shared prompt contract
  -> gold-set evaluation
  -> results.tsv
  -> docs/CURRENT_FRONTIER.md
```

## Components

- `edge_triage_core/`: side-effect-free shared product contract.
- `site/`: static public demo with curated offline scenarios and optional live preview affordance.
- `live_api.py`: optional guarded FastAPI endpoint for Live Gemma preview.
- `edge-triage-cli.py`: local field CLI for text/image/audio-style reports.
- `triage_sandbox.py`: research/evaluation harness.
- `results.tsv`: experiment ledger.
- `docs/CURRENT_FRONTIER.md`: public source of truth for current benchmark claims.
- `docs/superpowers/research_logs/`: historical EDG research logs and audit trail.

## Public mode

The public judge path is the static curated demo. It must work without model artifacts or a GPU.

## Optional live mode

The Live Gemma preview is guarded and may fail closed. It should never be the only way to evaluate the project.

## Research mode

The benchmark loop is separate from field startup. It owns data ingestion, model/artifact bootstrap, CUDA/VRAM guards, state hashing, and measured keep/discard decisions.
