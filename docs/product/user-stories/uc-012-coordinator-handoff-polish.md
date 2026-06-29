# UC-012: Coordinator Review and Handoff Polish

Status: implemented product story.

## Story

As a coordinator reviewing a volunteer triage card, I want a copyable radio script, a concise handoff summary, and a local review packet export, so that I can move the report into normal human-led coordination without treating Edge-Triage as dispatch authority.

## Acceptance criteria

- The Volunteer Field Console includes copy controls for the radio script and coordinator handoff summary.
- The console can export a single review packet for the latest triage card without network sync.
- The review packet includes the report, label, priority, safe next action, action pack, guidance basis, radio script, red flags, source, saved timestamp, and `synced: false`.
- The UI shows a review-before-use checklist covering location/source confirmation, red-flag review, and normal coordinator channels.
- The copy/export affordances preserve the safety boundary: no automatic sync, dispatch, diagnosis, or incident-command authority.
- Tests verify the static UI and JavaScript contract.

## Public-claims constraints

- This story is a local handoff aid, not an operational integration.
- Do not claim that exports were routed, delivered, acknowledged, or synced.
- Do not expose private operator runbook details in the public repository.
