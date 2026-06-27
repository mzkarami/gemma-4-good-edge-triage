# UC-008: Local Incident Queue and Export

Status: current implementation
Owner surface: volunteer console, CLI
Primary user: field volunteer / demo operator
Risk level: privacy and operational handoff

## Story

As a field volunteer, I want triage cards saved locally so that reports can be handed to a coordinator later without automatic network sync.

## Acceptance criteria

- Browser demo stores queued incidents in local storage.
- Browser demo can export the local queue as JSON.
- CLI can append JSONL records with `--save-case`.
- No automatic external sync is performed.
