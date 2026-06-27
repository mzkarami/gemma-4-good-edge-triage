# Edge-Triage Feature Backlog

Status: current product backlog.

## Implemented

### FB-001 Responder Action Pack

Structured do-not-do, collect-next, escalate-if, and route-to guidance attached to every triage result.

### FB-002 Red-flag escalation

Deterministic danger-sign scanner forces human-safety escalation for trapped people, unconscious/not-breathing cues, severe bleeding, live wires, gas/explosion hazards, structural collapse, rising water, and spreading fire.

### FB-003 Local incident queue/export

Volunteer console saves triage cards to a local browser queue and can export JSON without network sync. CLI can append JSONL records with `--save-case`.

### FB-004 Radio-script text mode

Shared core emits short English/Spanish radio scripts. CLI supports `--language` and `--format radio`.

### FB-005 Guidance basis

Shared core attaches deterministic conservative guidance snippets by label and red-flag state.

### FB-006 Judge walkthrough

Public site includes a walkthrough that compares curated demo, guarded live preview, CLI, local queue/export, and metrics evidence.

## Next candidates

- Private operator runbook for actual incident-queue handling.
- Copyable radio script and exported queue review affordances.
- Optional TTS only after text scripts are stable and reviewed.
