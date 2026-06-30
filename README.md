# Edge-Triage: Gemma 4 Multimodal Disaster Searcher

![Edge-Triage cover image](media/brand/edge-triage-cover-1200x675.jpg)

Edge-Triage is a local-first disaster triage system for the **Gemma 4 Good Hackathon**. It helps volunteers classify disaster reports from text and images on edge hardware, while data science teams use the same evaluation harness to keep improving the speed/accuracy frontier.

## What problem does it solve?

In a flood, wildfire, earthquake, or hurricane, responders receive messy reports from many sources: short text messages, photos, voice notes, social posts, and volunteer observations. Connectivity may be unreliable exactly when the report volume is highest.

Edge-Triage gives a field team a practical local tool:

1. A volunteer enters a short report, optionally with a photo.
2. Gemma 4 classifies the scene into a humanitarian triage category.
3. The app shows priority, confidence context, latency, a responder action pack, red-flag escalation when needed, guidance basis, and a conservative radio handoff script.
4. The responder keeps human control. Edge-Triage routes and explains; it does not replace incident command or medical professionals.

The project also gives a data science team a repeatable way to improve the system after new disaster data arrives:

1. Drop new MEDIC/QCRI-style shards or image/report samples into the workspace.
2. Run `triage_sandbox.py` against the 50-sample gold set.
3. Record F1, latency, VRAM, routing mix, state hash, and keep/discard status in `results.tsv`.
4. Compare new runs against the current frontier in `docs/CURRENT_FRONTIER.md`.
5. Keep changes only when they improve triage quality without breaking the field latency budget.

That split is the whole product: simple for volunteers, measurable for researchers.

The self-improving research loop is inspired by Andrej Karpathy's AutoResearch-style pattern: a fixed benchmark harness, an agent-editable sandbox, and a measured keep/discard rule. In Edge-Triage, that idea is adapted for NGO/humanitarian use through the templates in [`agents/`](agents/), with human review before deployment defaults change.

## Public evaluation experiences and model profiles

Edge-Triage has two public Web UI experiences. The Kaggle submission package is closed, but judges may still evaluate the submitted public links, so these routes should stay stable while the repository continues to improve:

- **Volunteer Mode:** the field-facing workflow for high-volume sorting. This is what a volunteer would use during an incident.
- **Optimization Mode:** the research cockpit showing autonomous experiments, keep/discard decisions, and the Pareto frontier. This is what a data science or response lead uses to understand why a profile was chosen.

Behind those experiences are two validated model profiles:

- **Volunteer Speed Profile:** optimized for fast routing when many reports arrive at once.
- **Critical Accuracy Profile:** optimized for high-stakes review, such as possible casualties, blocked evacuation routes, or other ambiguous reports where a small latency tradeoff is acceptable. It is not a third top-level UI mode; it appears in the metrics/frontier evidence so teams know when to choose the more careful profile.

The curated offline demo in `site/` works without a hosted model so judges always have a reliable path. It does not call the model or show upload controls; judges click fixed public-safe scenario cards and the UI updates the related image, label, priority, next action, and analysis. The optional Live Gemma preview can call the guarded Gemma 4 API for uploaded images through the public site, without requiring judges to paste a token.

## Current frontier

The public benchmark source of truth is [`docs/CURRENT_FRONTIER.md`](docs/CURRENT_FRONTIER.md). Use that file when updating public claims, the demo site, or the video script.

| Profile | Use case | F1 | Accuracy | Latency | Samples | Run |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Volunteer Speed Profile | High-volume field sorting | 0.9794 | see run log | 158.61 ms | 50 | EDG-307 r0 / `20260427T200056Z` |
| Critical Accuracy Profile | High-stakes review | 0.9818 | 0.9800 | 237.97 ms | 50 | EDG-480 r2 / `20260515T093558Z` |

Both profiles are far below the 4-second field-response budget. Older lower benchmark figures are historical milestones from earlier submission-era or ledger states, not the current frontier.

## How the pieces fit

```text
Field volunteer                  Data science / response lead
      |                                      |
      v                                      v
site/ or edge-triage-cli.py       triage_sandbox.py
      |                                      |
      v                                      v
Gemma 4 local triage              gold-set evaluation + results.tsv
      |                                      |
      v                                      v
label + priority + action         keep/discard frontier decision
```

Main artifacts:

- `edge_triage_core/` — shared product contract for prompts, labels, runtime defaults, and response shaping. This is intentionally lightweight: importing it must not load models, probe CUDA, download artifacts, or start the benchmark harness.
- `site/` — curated offline demo with Volunteer Mode, Optimization Mode, and readable metrics.
- `live_api.py` — optional guarded Live Gemma preview for uploaded images; consumes `edge_triage_core/` for shared labels/prompts while keeping HTTP guardrails local.
- `edge-triage-cli.py` — local field CLI for text/image/audio-style reports; consumes `edge_triage_core/` directly and no longer imports the research sandbox for basic startup/help.
- `triage_sandbox.py` — research and evaluation harness; consumes `edge_triage_core/` prompts while keeping benchmark/download/GPU lifecycle logic separate.
- `results.tsv` — experiment ledger.
- `docs/CURRENT_FRONTIER.md` — canonical public metric summary.
- `docs/superpowers/research_logs/` — public research trail for the AutoResearch/EDG experiment loop.
- `media/` — public-safe screenshots and source media for Kaggle/video.
- `data/` and `logs/` — placeholder workspaces for local shards, extracted images, and generated benchmark logs; generated contents stay ignored.
- `submission_notebook.ipynb`, `analysis.ipynb`, and `kaggle_dataset_upload/` — Kaggle packaging and research-ledger notebook assets.
- `agents/` — optional templates for Paperclip-style NGO/research workspaces that want an agentic AutoResearch loop around `triage_sandbox.py`.
- `plugin/` — optional Paperclip dashboard skeleton for viewing `results.tsv` and triggering trusted local benchmark pulses.
- `infra/` — optional local Paperclip stack example. The public judge demo does not require it.
- `Modelfile` and `litert_backend.py` — Ollama and LiteRT/Google AI Edge deployment scaffolds.

## Quick start

These commands are first-clone smoke checks. They do **not** need the multi-GB model/data downloads because they run tests, help screens, and the static judge site.

```bash
# Install dependencies
uv sync

# Run CI-safe validation
uv run python scripts/run_ci_tests.py

# Try the field CLI help
uv run python edge-triage-cli.py --help

# Run the research sandbox help
uv run python triage_sandbox.py --help

# Serve the static judge site locally
python3 -m http.server 4173 --directory site
# then open http://127.0.0.1:4173
```

To run real local model inference or a full research benchmark, prepare the model/data artifacts first. `prepare.py` checks sources in this order: attached Kaggle notebook inputs under `/kaggle/input`, local cache, optional Kaggle dataset slugs, then Hugging Face.

```bash
# Option A: Hugging Face source. Auth may be required for gated model/data access.
uv run huggingface-cli login
uv run prepare.py --source huggingface

# Option B: Kaggle source. Kaggle uses an API token rather than an interactive login.
# 1. Create/download kaggle.json from https://www.kaggle.com/settings/account
# 2. Put it at ~/.kaggle/kaggle.json and run: chmod 600 ~/.kaggle/kaggle.json
#    Alternative: export KAGGLE_USERNAME=<username> and KAGGLE_KEY=<api-key>
# 3. Verify the CLI is available:
uv run kaggle --version
# In a Kaggle notebook, attach the model/data datasets as Inputs and prepare.py will auto-detect them.
# Locally, set dataset slugs before running prepare.py:
# export EDGE_TRIAGE_KAGGLE_MODEL_DATASET=<kaggle-user>/<edge-triage-model-dataset-slug>
# export EDGE_TRIAGE_KAGGLE_DATASET=<kaggle-user>/<edge-triage-parquet-dataset-slug>
uv run prepare.py --source kaggle

# Option C: Auto source. This tries Kaggle inputs/cache/env first, then Hugging Face.
uv run prepare.py --source auto

# Extract local benchmark images/labels after artifacts are prepared.
uv run local_extractor.py

# Then run the field CLI or benchmark with real artifacts.
uv run python edge-triage-cli.py --report "Bridge damaged after flood; two families waiting near school."
uv run python triage_sandbox.py
```

For a safer public-style static site container:

```bash
docker compose up -d --build
curl -I http://127.0.0.1:4173/
curl -fsS http://127.0.0.1:4173/data.json >/dev/null
```

Optional full-stack smoke for reviewers and maintainers:

```bash
# Runs the static site plus guarded live API in credential-free fallback mode.
# This is opt-in so normal tests stay fast and do not require Docker services,
# Hugging Face credentials, Kaggle credentials, GPU, or model artifacts.
EDGE_TRIAGE_RUN_E2E=1 scripts/e2e_smoke.sh
```

## Documentation map

Start here if you are new:

- [`docs/README.md`](docs/README.md) — canonical documentation map and current/target/reference rules.
- [`instructions/README.md`](instructions/README.md) — team/agent operating layer, principles, testing expectations, and acceptance gate.
- [`docs/product/README.md`](docs/product/README.md) — product brief, roadmap, public-claims guidance, evaluation-window stability, and user stories.
- [`docs/product/user-stories/README.md`](docs/product/user-stories/README.md) — numbered field, judge, live-demo, research, and maintainer user stories.
- [`docs/architecture/README.md`](docs/architecture/README.md) — current architecture, runtime boundaries, data flow, diagrams, and ADRs.
- [`docs/testing/README.md`](docs/testing/README.md) — test strategy, validation reports, performance evidence, and CI checks.
- [`docs/operations/README.md`](docs/operations/README.md) — deployment/runbook indexes and public/private boundary guidance.
- [`docs/research/README.md`](docs/research/README.md) — current frontier, experiment ledger, and EDG research-log entrypoint.
- [`docs/submission/README.md`](docs/submission/README.md) — Kaggle writeups, video script, and public submission materials.
- [`docs/CURRENT_FRONTIER.md`](docs/CURRENT_FRONTIER.md) — current trusted metrics and how to talk about them.
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — public demo hosting, Docker, HTTPS, and live-preview safety controls.
- [`agents/README.md`](agents/README.md) — optional Paperclip-style agent templates for self-improving NGO/research workflows.
- [`plugin/README.md`](plugin/README.md) and [`infra/README.md`](infra/README.md) — optional local Paperclip dashboard/stack examples.
- [`data/README.md`](data/README.md) and [`logs/README.md`](logs/README.md) — local workspace placeholders and ignore policy.
- [`site/README.md`](site/README.md) and [`media/README.md`](media/README.md) — judge demo site and media library notes.

## Why it matters

- **Offline privacy:** sensitive disaster data can be processed locally.
- **Speed:** the default field profile is measured in hundreds of milliseconds in the validated benchmark, not seconds.
- **Safety:** outputs are constrained to triage labels and conservative next actions, not unsupported medical advice.
- **Adaptability:** the optimization loop can re-evaluate new crisis data and expose the accuracy/latency frontier.

---

Benchmark-driven development for local-first disaster triage.

Gemma is a trademark of Google LLC.
