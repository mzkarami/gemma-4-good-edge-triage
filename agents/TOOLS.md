# Project Toolbox: Edge-Triage Commands

These are the commands and tools the **Researcher Agent** uses within the local sandbox to evaluate and optimize the triage system.

## 1. Primary Evaluation
**Command:** `uv run triage_sandbox.py --description "<desc>"`
- **Output:** Performance metrics (F1-Score, Latency, VRAM).
- **Behavior:**
    - Detects shards in `data/` or cache.
    - Runs `local_extractor.py` if shards are found.
    - Computes `state_hash` for efficiency skip.
    - Appends metrics and your `<desc>` to `results.tsv`.

## 2. One-Time Setup / Cleanup
- **`uv run prepare.py`**: Downloads training data shards and trains the base BPE tokenizer.
- **`uv run local_extractor.py`**: Manually triggers image/metadata extraction from `.parquet` shards.
- **`uv run download_litert.py`**: Downloads the official Google AI Edge `.litertlm` models.

## 3. Git Operations (State Management)
- **`git checkout -b autoresearch/<tag>`**: Creates a new experimental branch.
- **`git commit -am "experiment: <desc>"`**: Commits a new iteration.
- **`git reset --hard HEAD~1`**: Discards a failed experiment (regression).
- **`git merge main`**: Pulls the latest infrastructure updates.

## 4. Resource Monitoring
- **`nvidia-smi`**: Monitors VRAM usage and GPU temperature.
- **`top` / `htop`**: Monitors CPU and system memory usage.
- **`du -sh data/`**: Monitors storage used by active images and shards.
