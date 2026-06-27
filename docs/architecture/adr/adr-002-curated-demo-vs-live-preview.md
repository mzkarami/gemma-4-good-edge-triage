# ADR-002: Curated Demo and Live Gemma Preview Separation

Status: Accepted
Date: 2026-06-27

## Context

Public judges need a reliable experience that does not depend on GPU availability, model artifacts, or live inference health. The project also benefits from an optional live preview when the model service is available.

## Decision

Keep the curated static demo as the reliable default public path. Keep Live Gemma preview optional, same-origin, guarded, and fail-closed.

## Consequences

- The public demo works without model infrastructure.
- Live inference can be disabled or rate-limited without breaking evaluation.
- Public copy must clearly distinguish curated/offline behavior from live inference.
