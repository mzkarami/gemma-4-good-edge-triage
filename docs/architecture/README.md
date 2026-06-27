# Edge-Triage Architecture

Status: canonical architecture index.

This directory describes current runtime boundaries, deployment boundaries, research-loop architecture, and architecture decisions.

## Start here

- [Current architecture](current-architecture.md) - product paths, research path, and component overview.
- [Runtime boundaries](runtime-boundaries.md) - `edge_triage_core`, CLI, Live API, sandbox, and import rules.
- [Data flow](data-flow.md) - report/image/model/data lifecycle and public/private data boundaries.
- [Live API security boundary](live-api-security-boundary.md) - upload, rate, timeout, and fail-closed controls.
- [Research loop architecture](research-loop-architecture.md) - state hash, benchmark, results ledger, and frontier promotion.
- [Architecture diagrams](diagrams.md) - ASCII views for quick orientation.
- [ADRs](adr/README.md) - architecture decision records.

## Current vs target architecture

Each architecture doc should label whether it describes current implementation, target/future direction, or reference/historical context. Do not treat future LiteRT/mobile/NPU/Paperclip ideas as current behavior unless implemented and verified.

## Compatibility note

The older top-level [ARCHITECTURE.md](../ARCHITECTURE.md) remains as a short public overview. New architecture decisions and deeper runtime details should live here.
