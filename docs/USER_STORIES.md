# Edge-Triage User Stories

These stories describe the product behavior after the shared-core refactor. They are not new benchmark claims; metrics still come from `docs/CURRENT_FRONTIER.md`.

## Field Volunteer

As a field volunteer, I want to enter a short disaster report and optionally attach a local photo, so that I can get a constrained triage label, priority, and conservative next action without depending on cloud connectivity.

Acceptance notes:
- The CLI uses `edge_triage_core/` for prompt, label, and runtime defaults.
- Showing CLI help or starting argument parsing must not import `triage_sandbox.py` or trigger benchmark/model artifact bootstrapping.
- The output remains decision support only, not medical or incident-command authority.

## Public Judge / Reviewer

As a public judge, I want the demo site to work even if live inference is unavailable, so that I can evaluate the product narrative, metrics, and curated scenarios reliably.

Acceptance notes:
- `site/` remains a static curated/offline path backed by `site/data.json`.
- The optional Live Gemma preview is separate and can fail closed without breaking the curated showcase.
- Public claims stay aligned with `docs/CURRENT_FRONTIER.md`.

## Live Demo Operator

As a demo operator, I want the Live API to share labels/prompts with the CLI while keeping HTTP guardrails local, so that the public endpoint is consistent but still hardened for uploads.

Acceptance notes:
- `live_api.py` imports shared label/prompt/result helpers from `edge_triage_core/`.
- Upload size, MIME validation, image sanitization, rate/day limits, concurrency cap, timeout, and kill switch remain in `live_api.py`.
- The API returns bounded JSON without raw model traces or retained uploads.

## Research / Response Lead

As a research lead, I want the benchmark harness to use the same product prompt contract as the field surfaces, so that optimization results stay connected to what users actually run.

Acceptance notes:
- `triage_sandbox.py` imports shared prompt constants from `edge_triage_core/`.
- Benchmark, artifact download, local extraction, CUDA/VRAM guards, routing experiments, and `results.tsv` logging remain in `triage_sandbox.py`.
- Human review is still required before agent-discovered changes become deployment defaults.

## Maintainer

As a maintainer, I want import-boundary tests around the CLI and core package, so that future refactors do not accidentally re-couple product startup to the research harness.

Acceptance notes:
- Tests assert `edge_triage_core` does not import heavy modules such as `triage_sandbox`, `llama_cpp`, `torch`, `prepare`, or `local_extractor`.
- Tests assert CLI import/help does not trigger sandbox startup.
- Full verification remains `uv run python -m unittest discover tests/` plus CLI and sandbox help smokes.
