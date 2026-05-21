# Heartbeat: The Optimization Routine

This document defines the recurring schedule that triggers the **Researcher Agent** within the Paperclip workspace.

## 1. Pulse Configuration
The agent wakes up once per hour (at the top of the hour) to check for a new state (new code, new shards, or a new optimization prompt).

- **Schedule:** `0 * * * *` (Hourly)
- **Timezone:** `UTC`
- **Concurrency Policy:** `skip_if_active` (If an experiment is still running, do not start a new one).
- **Catch-up Policy:** `skip_missed` (Do not run back-to-back if the server was offline).

## 2. Trigger Strategy
The Paperclip routine triggers a "Pulse" task that tells the agent to:
1.  **Observe:** Check for any new `.parquet` shards in `~/.cache/autoresearch/data/` or `./data/`.
2.  **Pull:** `git pull` the latest research goals from the `main` branch.
3.  **Evaluate:** Compute the current `state_hash`.
4.  **Experiment:** Run the `uv run triage_sandbox.py` benchmark.
5.  **Refine:** If metrics drop, the agent iterates on the `triage_sandbox.py` prompts.

## 3. Self-Healing
If the routine encounters a "Blocked" state (e.g., missing data, GPU out of memory), it will:
1.  **Notify:** Post a comment to the Paperclip task.
2.  **Attempt Reset:** Try to run `uv run prepare.py` to restore the base datasets.
3.  **Halt:** If recovery fails, it pauses the routine and waits for a human to intervene.
