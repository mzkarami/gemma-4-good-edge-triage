# ADR-004: Responder Action Packs and Red-Flag Overrides

Status: Accepted
Date: 2026-06-27

## Context

Internal product review identified grounded guidance, danger-sign overrides, offline queues, and local-language scripts as useful field-workflow patterns. Edge-Triage needed these without becoming a generic emergency chatbot.

## Decision

Add shared-core response enrichment:

- `edge_triage_core/actions.py` for responder action packs.
- `edge_triage_core/safety.py` for deterministic red-flag overrides.
- `edge_triage_core/language.py` for scoped radio scripts.

Keep automatic sync, TTS, and RAG out of this slice.

## Consequences

- CLI, Live API, and demo share safer operational guidance.
- Tests must cover red-flag override behavior.
- Public copy must frame the output as human-reviewed decision support.
