# UC-004: Research Response Lead Optimization

Status: current implementation
Owner surface: `triage_sandbox.py`, `results.tsv`, `docs/CURRENT_FRONTIER.md`
Primary user: research / response lead
Risk level: benchmark/public-claims integrity

## Story

As a research lead, I want the benchmark harness to use the same product prompt contract as the field surfaces, so that optimization results stay connected to what users actually run.

## Current implementation

- `triage_sandbox.py` imports shared prompt constants from `edge_triage_core/`.
- Benchmark, artifact download, local extraction, CUDA/VRAM guards, routing experiments, and `results.tsv` logging remain sandbox-owned.

## Acceptance criteria

- Comparable runs are clearly separated from diagnostic or blocked runs.
- Public frontier updates require evidence.
- Human review remains required before agent-discovered changes become deployment defaults.

## Verification

```bash
uv run python triage_sandbox.py --help
uv run python -m unittest tests.test_triage_sandbox -v
```
