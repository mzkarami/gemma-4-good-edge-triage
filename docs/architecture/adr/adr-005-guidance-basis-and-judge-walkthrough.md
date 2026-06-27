# ADR-005: Guidance Basis and Judge Walkthrough

Status: Accepted
Date: 2026-06-27

## Context

Edge-Triage now returns action packs, red-flag escalation, queue/export records, and radio scripts. Judges and maintainers need to see that these surfaces share one human-led safety contract and that action guidance is deterministic rather than improvised.

## Decision

Add deterministic guidance-basis snippets under `edge_triage_core/guidance.py`, expose `guidance_basis` through shared response shaping, and add a public judge walkthrough page comparing curated demo, guarded live preview, CLI, local queue/export, and metrics evidence.

## Consequences

- The product explains why conservative next actions were chosen.
- The walkthrough improves review clarity without adding model/runtime risk.
- Guidance snippets must remain conservative and cannot become medical advice, automatic dispatch, or incident-command authority.
