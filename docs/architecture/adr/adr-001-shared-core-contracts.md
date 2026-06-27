# ADR-001: Shared Core Contracts

Status: Accepted
Date: 2026-06-27

## Context

The field CLI previously depended on the research sandbox for shared prompt/config behavior. That coupled field startup to benchmark and artifact lifecycle concerns.

## Decision

Create `edge_triage_core/` as the shared, side-effect-free product contract for prompts, labels, runtime defaults, fallback classification, and response shaping.

The CLI, Live API, and sandbox may consume the core. Product surfaces must not import `triage_sandbox.py` for startup/help.

## Consequences

- Field startup is lighter and safer.
- Shared labels/prompts stay aligned across product and benchmark surfaces.
- Import-boundary tests are required.
- Benchmark/artifact/CUDA logic remains sandbox-local.

## Verification

- `tests/test_edge_triage_core.py`
- `tests/test_cli_import_boundary.py`
- `uv run python edge-triage-cli.py --help`
