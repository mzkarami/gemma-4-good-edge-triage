# Edge-Triage Project Overview and Vision

Edge-Triage is a local-first disaster triage system for classifying messy field reports from text and images. It pairs a simple field-facing volunteer workflow with a measured research loop that can improve the speed/accuracy frontier over time.

## Product split

- **Field product:** static web demo, optional guarded Live Gemma preview, and `edge-triage-cli.py` for local triage.
- **Research system:** `triage_sandbox.py`, `results.tsv`, `docs/CURRENT_FRONTIER.md`, and EDG research logs.
- **Shared contract:** `edge_triage_core/` for prompts, labels, runtime defaults, fallback classification, and response shape.

## Vision

A responder should be able to run constrained triage locally, without sending sensitive disaster reports to a cloud service by default. A research lead should be able to measure whether a change improves humanitarian triage quality without relying on subjective impressions.

## Non-goals

- Replacing incident command.
- Giving medical advice.
- Turning public demo copy into unsupported benchmark claims.
- Exposing private infrastructure or sensitive disaster data in the public repo.
