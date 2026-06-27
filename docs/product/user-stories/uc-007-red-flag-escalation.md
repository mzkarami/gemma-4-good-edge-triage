# UC-007: Red-Flag Escalation

Status: current implementation
Owner surface: `edge_triage_core/safety.py`
Primary user: field volunteer / maintainer
Risk level: critical safety

## Story

As a maintainer, I want deterministic red-flag escalation for clear danger signs so that obvious trapped-person, electrical, gas, fire, collapse, or rising-water cues do not depend only on model classification.

## Acceptance criteria

- Red flags are detected before response shaping completes.
- A red flag can force the label to `affected_injured_or_dead_people`.
- Responses expose `red_flags` and `red_flag_escalation`.
- Tests cover the override path.
