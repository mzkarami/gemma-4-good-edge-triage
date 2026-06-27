# UC-005: Maintainer Import Boundary

Status: current implementation
Owner surface: `edge_triage_core/`, tests
Primary user: maintainer / contributor
Risk level: architecture drift

## Story

As a maintainer, I want import-boundary tests around the CLI and core package, so that future refactors do not accidentally re-couple product startup to the research harness.

## Current implementation

- Tests assert `edge_triage_core` does not import heavy modules such as `triage_sandbox`, `llama_cpp`, `torch`, `prepare`, or `local_extractor`.
- Tests assert CLI import/help does not trigger sandbox startup.

## Acceptance criteria

- Core imports are side-effect free.
- CLI help remains lightweight.
- Product surfaces depend on core, not sandbox.

## Verification

```bash
uv run python -m unittest tests.test_edge_triage_core tests.test_cli_import_boundary -v
```
