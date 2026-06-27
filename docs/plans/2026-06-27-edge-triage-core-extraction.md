# Edge-Triage Core Extraction Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Split shared field/live/sandbox triage contracts out of `triage_sandbox.py` so the field CLI and live API do not depend on the research harness at import time.

**Architecture:** Add a small `edge_triage_core/` package for pure constants, prompt selection, label metadata, runtime config, and response helpers. Keep benchmark/download/evaluation behavior in `triage_sandbox.py`; make CLI and live API consume the shared core directly. Preserve public metrics, prompt behavior, and deployment defaults.

**Tech Stack:** Python 3.11, unittest, FastAPI, llama-cpp-python, uv.

---

### Task 1: Capture baseline behavior

**Objective:** Prove the repo is green before refactoring.

**Files:**
- Read: `README.md`, `docs/ARCHITECTURE.md`, `docs/DEVELOPER_GUIDE.md`, `edge-triage-cli.py`, `live_api.py`, `triage_sandbox.py`

**Steps:**
1. Run `uv run python -m unittest discover tests/`.
2. Run `uv run python edge-triage-cli.py --help`.
3. Run `uv run python triage_sandbox.py --help`.
4. Record any pre-existing untracked files and do not include IDE files in commits.

### Task 2: Add shared core package

**Objective:** Create pure modules that have no heavy imports and no model/data side effects.

**Files:**
- Create: `edge_triage_core/__init__.py`
- Create: `edge_triage_core/prompts.py`
- Create: `edge_triage_core/labels.py`
- Create: `edge_triage_core/config.py`
- Create: `edge_triage_core/results.py`
- Test: `tests/test_edge_triage_core.py`

**Contracts:**
- `prompts.py` owns canonical labels, system prompt, main prompt variants, and prompt resolution from `TRIAGE_MAIN_PROMPT_VARIANT`.
- `labels.py` owns label metadata, safe text sanitization, label parsing, fallback classification, and fallback scene summaries.
- `config.py` owns model path/env defaults and `TriageRuntimeConfig.from_env()`.
- `results.py` owns `build_triage_response()`.
- Importing `edge_triage_core` must not import `triage_sandbox`, `llama_cpp`, `torch`, `prepare`, or `local_extractor`.

### Task 3: Refactor the field CLI boundary

**Objective:** Make CLI help/startup independent of `triage_sandbox.py`.

**Files:**
- Modify: `edge-triage-cli.py`
- Modify: `tests/test_field_tool.py`
- Create: `tests/test_cli_import_boundary.py`

**Contracts:**
- `edge-triage-cli.py --help` must not import `triage_sandbox`.
- Runtime model loading may still import `llama_cpp` only inside execution path.
- CLI prompt text must match `edge_triage_core.prompts.resolve_main_prompt_template()`.

### Task 4: Refactor live API shared contracts

**Objective:** Remove duplicated prompts, label metadata, fallback classification, parsing, and response construction from `live_api.py`.

**Files:**
- Modify: `live_api.py`
- Modify: `tests/test_live_api.py`
- Modify: `tests/test_live_api_security_controls.py` only if needed

**Contracts:**
- Existing live API tests remain green.
- Public fallback behavior remains unchanged.
- Security controls remain in `live_api.py`.

### Task 5: Refactor sandbox prompt/config imports safely

**Objective:** Make the research harness consume shared core constants without changing evaluation behavior.

**Files:**
- Modify: `triage_sandbox.py`
- Modify: `tests/test_triage_sandbox.py` only if assertions require import-source updates

**Contracts:**
- Keep all targeted probe prompts and benchmark routing logic in `triage_sandbox.py`.
- Keep artifact download/bootstrap behavior in `triage_sandbox.py`.
- `TRIAGE_PROMPT_TEMPLATE`, `TRIAGE_SYSTEM_PROMPT`, `MODEL_PATH`, `MMPROJ_PATH`, `N_CTX`, and `N_GPU_LAYERS` remain available as module attributes for legacy tests and scripts.

### Task 6: Update docs and user-facing guides

**Objective:** Keep architecture, developer, operations, and README docs aligned.

**Files:**
- Modify: `README.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/DEVELOPER_GUIDE.md`
- Modify: `docs/OPERATIONS_GUIDE.md`
- Modify: `site/README.md` if needed

**Docs must explain:**
- `edge_triage_core/` is the shared product contract.
- CLI/live API/sandbox all consume core.
- Research harness remains the benchmark and experiment loop.
- Public metrics still come from `docs/CURRENT_FRONTIER.md`.

### Task 7: Verify and commit

**Objective:** Prove the refactor is behavior-preserving and commit a clean slice.

**Commands:**
- `uv run python -m unittest discover tests/`
- `uv run python edge-triage-cli.py --help`
- `uv run python triage_sandbox.py --help`
- Optional live/static smoke if deployment files changed.

**Commit:**
- `git add edge_triage_core tests edge-triage-cli.py live_api.py triage_sandbox.py README.md docs/ARCHITECTURE.md docs/DEVELOPER_GUIDE.md docs/OPERATIONS_GUIDE.md docs/plans/2026-06-27-edge-triage-core-extraction.md`
- `git commit -m "refactor: extract shared edge triage core"`
