# Developer Guide: Setting Up Edge-Triage

Welcome to the **Edge-Triage Hybrid Searcher** development guide. This document will help you get the project running on your local machine for further research or deployment.

## 1. Prerequisites
*   **Operating System:** Linux (Ubuntu 22.04+ recommended) or macOS.
*   **Python:** 3.11+ (Managed via `uv`).
*   **Hardware:** 8GB+ RAM. A GPU is recommended but not required (we have optimized for CPU execution).
*   **Tooling:** Install [uv](https://github.com/astral-sh/uv) for lightning-fast dependency management.

## 2. Fast Setup
```bash
# 1. Clone the repository
git clone https://github.com/mzkarami/gemma-4-good-edge-triage.git
cd gemma-4-good-edge-triage

# 2. Sync dependencies
uv sync

# 3. Authenticate with Hugging Face (Needed for dataset/model access)
uv run huggingface-cli login
```

## 3. Preparing Data & Models
The project uses **QCRI/MEDIC** for multimodal triage and **Gemma 4 GGUF/LiteRT** for local inference.

`prepare.py` is source-flexible for judges and developers:

1. Kaggle notebook Inputs under `/kaggle/input` are scanned first.
2. Existing local cache files under `~/.cache/autoresearch/` are reused.
3. If `EDGE_TRIAGE_KAGGLE_MODEL_DATASET` or `EDGE_TRIAGE_KAGGLE_DATASET` are set, the Kaggle CLI is used as a fallback source.
4. Hugging Face is used last.

```bash
# Optional Hugging Face source.
uv run huggingface-cli login
uv run prepare.py --source huggingface

# Optional Kaggle source for users without a Hugging Face account.
# Kaggle uses an API token rather than interactive login:
# - download kaggle.json from https://www.kaggle.com/settings/account to ~/.kaggle/kaggle.json
# - chmod 600 ~/.kaggle/kaggle.json
# - verify with: uv run kaggle --version
# In a Kaggle notebook, attach the datasets as Inputs instead of setting these.
# Locally, set your published dataset slugs:
# export EDGE_TRIAGE_KAGGLE_MODEL_DATASET=<kaggle-user>/<edge-triage-model-dataset-slug>
# export EDGE_TRIAGE_KAGGLE_DATASET=<kaggle-user>/<edge-triage-parquet-dataset-slug>
uv run prepare.py --source kaggle

# Auto source tries Kaggle inputs/cache/env first, then Hugging Face.
uv run prepare.py --source auto

# Continue with local extraction.
uv run download_litert.py

# Extract the local Gold Set (Images + Labels)
uv run local_extractor.py
```

**Note on Autonomous Setup:** The `triage_sandbox.py` now includes an **Autonomous Bootloader**. If you run the sandbox and the main GGUF model or `mmproj-F16.gguf` multimodal projector are missing or misnamed, it will autonomously trigger the downloader and apply the mandatory `Edge-Triage-` prefix to comply with naming guidelines. The public live API container still expects these artifacts to already be mounted under `/app/models`; run `uv run prepare.py` or otherwise populate `~/.cache/autoresearch/models/` before enabling live model mode.

## 4. Data Strategy: Local vs. Global Cache
Edge-Triage uses a "Hybrid Data Strategy" to balance high-performance research with easy deployment:

1.  **Global Cache (`~/.cache/autoresearch/`):**
    *   **Models:** Multi-GB weights (GGUF, LiteRT) are stored here once.
    *   **Tokenizer:** Shared BPE tokenizer assets.
    *   **Purpose:** Prevents redundant downloads across different project versions.

2.  **Local Workspace (`data/`):**
    *   **Raw Shards:** Drop `.parquet` files here for ingestion.
    *   **Gold Set:** The active `gold_set.json` used for the current benchmark.
    *   **Active Images:** The `data/images/` folder contains only the images needed for the current run.
    *   **Archive:** Processed shards are automatically moved to `data/archive/` post-run.
    *   **Purpose:** Enables the "Zero-Touch" autonomous lifecycle (extraction, hashing, and purging) without affecting the global system state.

## 5. Running Experiments
The `triage_sandbox.py` is the main entry point for research. It measures **Accuracy (F1)** and **Latency**.

```bash
# Run the current best configuration (Vision + Multimodal)
mkdir -p logs
uv run triage_sandbox.py > logs/run.log 2>&1
```

Keep generated logs under `logs/`, not in the project root. Named experiment logs should follow the same pattern, for example `logs/run_edg479_r1.log`. The repository keeps `logs/.gitkeep` for fresh checkouts, while generated `*.log` files stay ignored.

## 6. Runtime Boundary Architecture
The product surfaces share one lightweight core package:

- `edge_triage_core/prompts.py` owns the canonical prompt variants and system prompt used by the CLI and research harness. The Live API uses a JSON-bounded prompt from the same package.
- `edge_triage_core/labels.py` owns canonical labels, priority/next-action metadata, safe text sanitization, and guarded fallback classification.
- `edge_triage_core/config.py` owns model path and runtime defaults without loading models or downloading artifacts.
- `edge_triage_core/results.py` owns the common response shape.

This package must remain side-effect free. Importing it should not import `triage_sandbox.py`, `llama_cpp`, `torch`, `prepare.py`, or `local_extractor.py`. The field CLI and live API consume this shared contract directly; the research sandbox consumes it while keeping benchmark, artifact, and CUDA lifecycle code local to `triage_sandbox.py`.

## 7. Dual-Path Architecture
The project is split into two primary workflows:

1. **The Research Sandbox (`triage_sandbox.py`)**: 
   - Used by the **Researcher Agent** to autonomously optimize prompt templates and reasoning steps.
   - Imports shared prompt constants from `edge_triage_core/` so product and benchmark surfaces stay aligned.
   - Logs results to `results.tsv`.
   
2. **The Field CLI (`edge-triage-cli.py`)**:
   - A simplified tool for volunteers on the ground.
   - Imports prompt/runtime contracts from `edge_triage_core/`, not from `triage_sandbox.py`, so help/startup stays lightweight and does not trigger benchmark bootstrapping.

## 8. Deployment Backends
We support three high-performance edge backends:

### A. Ollama (One-Click)
```bash
ln -s ~/.cache/autoresearch/models/Edge-Triage-gemma-4-E4B-it-UD-Q2_K_XL.gguf .
ollama create edge-triage -f Modelfile
ollama run edge-triage
```
*   **Current frontier:** use `docs/CURRENT_FRONTIER.md` for competition-facing metrics. The current validated full-50 profiles are Volunteer Speed Profile (`0.9794` F1 at `158.61 ms`) and Critical Accuracy Profile (`0.9818` F1 at `237.97 ms`), both under the 4s field budget.

### B. LiteRT-LM (Google AI Edge)
```bash
# Run with the native .litertlm model (for mobile/NPU hardware)
litert-lm run ~/.cache/autoresearch/models/Edge-Triage-gemma-4-E2B-it.litertlm --prompt "Triage: Flood in district."
```

### C. llama.cpp (Research & Vision)
Native high-fidelity support provided via `llama-cpp-python` in `triage_sandbox.py` and the `edge-triage-cli.py`.

## 9. Self-Improving Agent Templates
Edge-Triage includes optional agent templates under [`agents/`](../agents/). They are meant for teams that want to connect a Paperclip-style NGO or research workspace to the benchmark loop.

The pattern is inspired by Andrej Karpathy's AutoResearch-style idea: give an agent a sandbox, a fixed evaluation harness, and a keep/discard rule, then let measured experiments improve the system over time. Edge-Triage adapts that idea for humanitarian triage, with stricter latency, safety, and human-review constraints.

Start here:

* [`agents/README.md`](../agents/README.md) explains how the templates fit together.
* [`agents/AGENTS.md`](../agents/AGENTS.md) defines the Researcher and Librarian roles.
* [`agents/SOUL.md`](../agents/SOUL.md) gives the Researcher Agent its operating loop.
* [`agents/TOOLS.md`](../agents/TOOLS.md) lists the allowed benchmark/setup commands.
* [`agents/HEARTBEAT.md`](../agents/HEARTBEAT.md) shows an hourly automation schedule you can adapt.
* [`plugin/README.md`](../plugin/README.md) explains the optional local dashboard skeleton.
* [`infra/README.md`](../infra/README.md) explains the optional local Paperclip stack.
* [`data/README.md`](../data/README.md) and [`logs/README.md`](../logs/README.md) describe public-safe local workspaces.
* [`docs/superpowers/research_logs/README.md`](superpowers/research_logs/README.md) is the public audit trail for the EDG experiment loop.

In this repository, the self-improving loop is intentionally benchmark-gated:

* **Continuous Optimization:** The `triage_sandbox.py` can be edited by a Researcher Agent to test prompt variations, routing rules, and reasoning changes.
* **Self-Benchmarking:** Every proposed change is validated against the fixed gold-set evaluation path from `prepare.py` and recorded in `results.tsv`.
* **Human-Controlled Promotion:** Agent-discovered improvements should be reviewed through a branch or pull request before they become deployment defaults.

## 10. Submitting Changes
1.  Always run a full 50-sample benchmark to verify your changes.
2.  Log your results in `results.tsv` using this schema:

| Column | Description |
|--------|-------------|
| `run_id` | UTC timestamp id for the run (`YYYYMMDDTHHMMSSZ`) |
| `state_hash` | Hash of prompt + gold set + active image payload |
| `model` | The specific model variant used (e.g., Edge-Triage-gemma-4-E4B-it-UD-Q2_K_XL.gguf) |
| `f1_score` | F1 score from `evaluate_triage` |
| `latency_ms` | Average per-sample latency in milliseconds |
| `vram_gb` | Peak CUDA allocation in GB (0 on CPU-only runs) |
| `total_samples` | Number of evaluated samples |
| `status` | `keep`, `skip`, `blocked`, `crash`, or `legacy` |
| `description` | Human-readable run note or remediation guidance |

3.  Open a branch for substantial changes, or commit directly only when intentionally preparing the final submission package.

---
*Gemma is a trademark of Google LLC.*
