# UC-006: Responder Action Pack

Status: current implementation
Owner surface: shared core, CLI, Live API, static/volunteer demo
Primary user: field volunteer / coordinator
Risk level: humanitarian-safety guidance

## Story

As a field volunteer, I want a compact action pack after triage so that I know what to collect, what not to do, and when to escalate without treating the model as incident command.

## Acceptance criteria

- Every response includes `action_pack`.
- The action pack includes safe action, do-not-do, collect-next, escalate-if, and route-to fields.
- UI and CLI surface the action pack as decision support only.
