# Runtime Boundaries

Status: current implementation rule.

## Boundary summary

```text
edge_triage_core/        pure shared contract
edge-triage-cli.py       local field interface
live_api.py              HTTP/security boundary
triage_sandbox.py        research and benchmark harness
prepare.py               artifact/data source preparation
local_extractor.py       local benchmark extraction
```

## `edge_triage_core/`

Owns shared product contracts:

- prompt variants and system prompts;
- canonical labels;
- label metadata and fallback classification;
- runtime config defaults;
- response shaping helpers;
- responder action packs;
- deterministic red-flag escalation;
- scoped radio-script formatting.

Must not:

- import `triage_sandbox.py`;
- import `llama_cpp`, `torch`, `prepare.py`, or `local_extractor.py`;
- load models;
- download artifacts;
- probe CUDA/VRAM;
- write files or mutate benchmark state on import.

## `edge-triage-cli.py`

Owns local field UX. It may import `edge_triage_core/` at startup and should defer heavy model imports until an actual triage run. CLI help must remain lightweight and safe.

## `live_api.py`

Owns HTTP-specific guardrails:

- upload size and MIME validation;
- image decode/re-encode/sanitization;
- text-note sanitization;
- rate/day limits;
- concurrency cap;
- model timeout;
- kill switch;
- safe JSON errors.

It consumes shared labels/prompts/results from `edge_triage_core/`.

## `triage_sandbox.py`

Owns research behavior:

- artifact bootstrap;
- local extraction/data lifecycle;
- CUDA/VRAM guards;
- state hash;
- routing experiments;
- benchmark execution;
- `results.tsv` writes.

It may consume core prompt contracts, but product surfaces must not depend on it for startup.

## Verification

Runtime boundaries are guarded by:

```bash
uv run python -m unittest tests.test_cli_import_boundary tests.test_edge_triage_core -v
uv run python edge-triage-cli.py --help
```
