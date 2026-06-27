# UC-001: Field Volunteer Triage

Status: current implementation
Owner surface: `edge-triage-cli.py`, static demo
Primary user: field volunteer / responder
Risk level: high humanitarian-safety sensitivity

## Story

As a field volunteer, I want to enter a short disaster report and optionally attach a local photo, so that I can get a constrained triage label, priority, and conservative next action without depending on cloud connectivity by default.

## Current implementation

- CLI uses `edge_triage_core/` for prompt, label, and runtime defaults.
- CLI help/startup does not import `triage_sandbox.py`.
- Static demo presents curated public-safe scenarios.

## Acceptance criteria

- Output remains decision support only.
- CLI help runs without model artifact bootstrap.
- Local input files remain local to the operator machine.
- Labels stay within the canonical humanitarian category set.

## Verification

```bash
uv run python edge-triage-cli.py --help
uv run python -m unittest tests.test_cli_import_boundary tests.test_field_tool -v
```
