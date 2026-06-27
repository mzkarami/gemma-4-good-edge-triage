# UC-009: Radio Script Mode

Status: current implementation
Owner surface: shared core, CLI, volunteer console
Primary user: field volunteer / radio operator
Risk level: communication clarity

## Story

As a volunteer, I want a short radio-ready handoff script so that I can communicate the triage result clearly over low-bandwidth channels.

## Acceptance criteria

- Shared core emits `radio_script`.
- CLI supports `--format radio`.
- Spanish text mode is available as a scoped proof point, not broad dialect support.
- Output remains decision support and requires human review.
