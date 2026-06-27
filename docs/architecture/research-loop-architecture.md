# Research Loop Architecture

Status: current implementation.

Edge-Triage uses a measured research loop inspired by AutoResearch-style workflows: fixed harness, editable sandbox, benchmark evidence, and keep/discard decisions.

## Loop

```text
prepare artifacts/data
  -> extract or restore gold-set inputs
  -> compute state hash
  -> skip known duplicate or blocked states
  -> run comparable benchmark
  -> record metrics in results.tsv
  -> promote only when frontier evidence improves
```

## Key artifacts

- `triage_sandbox.py`: benchmark harness and routing experiments.
- `prepare.py`: source-flexible model/data preparation.
- `local_extractor.py`: local gold-set extraction.
- `results.tsv`: experiment ledger.
- `docs/CURRENT_FRONTIER.md`: public metric source of truth.
- `docs/superpowers/research_logs/`: EDG experiment history.

## Comparable run rules

A run should not become a public frontier claim if it is CPU fallback, missing telemetry, reduced GPU layers, partial sample count, or otherwise marked non-comparable.

## Promotion rule

Public claims should change only when `results.tsv`, logs, and `docs/CURRENT_FRONTIER.md` agree and the update is documented in a validation report.
