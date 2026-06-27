# UC-010: Deterministic Guidance Basis

Status: current implementation
Owner surface: shared core, Live API, CLI, volunteer console
Primary user: field volunteer / reviewer
Risk level: safety and claim clarity

## Story

As a reviewer, I want each triage card to show the conservative guidance basis behind its action pack so that the product is understandable without treating the model as incident command.

## Acceptance criteria

- Shared responses include `guidance_basis`.
- Red-flag responses prepend red-flag guidance.
- Guidance snippets are deterministic and label-based.
- Guidance text avoids medical, legal, dispatch, and incident-command authority.
