# Edge-Triage Autonomous Research

This is an experiment to have the Researcher Agent autonomously find the optimal disaster triage strategy using Gemma 4.

## Setup

To set up a new experiment, work with the user to:

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `apr10-triage`).
2. **Create the branch**: `git checkout -b autoresearch/<tag>` from current main.
3. **Read the in-scope files**:
   - `README.md` — repository context.
   - `prepare.py` — fixed evaluation harness and data loaders. Do not modify.
   - `triage_sandbox.py` — the file you modify. Prompt templates and reasoning loop.
4. **Verify data exists**: Check that `~/.cache/autoresearch/triage_data/` contains `gold_set.json`.
5. **Initialize results.tsv**: Ensure `results.tsv` is in the correct 8-column format. If it already exists, do not wipe it; the system will autonomously append new results.
6. **Confirm and go**: Confirm setup looks good and kick off experimentation.

## Experimentation

Each experiment runs locally using **llama-cpp-python**. You launch it simply as: `uv run triage_sandbox.py`.

**What you CAN do:**
- Modify `triage_sandbox.py` — this is the only file you edit. Everything is fair game: prompt templates, reasoning steps (e.g., Chain of Thought), and model parameters (context length, layers).

**What you CANNOT do:**
- Modify `prepare.py`. It is read-only. It contains the fixed evaluation logic and ground truth data.
- Install new packages. Use what's in `pyproject.toml`.

**The goal is simple: maximize Triage F1-Score while staying under a 4000ms (4s) latency budget.**

**Latency constraint**: First responders need fast results. Any strategy that averages > 4 seconds per triage is considered a failure (discard).

**VRAM constraint**: Must fit on a standard laptop (target < 8GB peak VRAM).

**Simplicity criterion**: Simpler is better. A 0.01 F1-score gain that adds massive complexity is usually not worth it.

## Logging results

When an experiment is done, log it to `results.tsv` (tab-separated).

Columns:
```
run_id	state_hash	model	f1_score	latency_ms	vram_gb	total_samples	status	description
```

1. run_id (timestamp)
2. state_hash (MD5 of experimental parameters)
3. model (filename of the GGUF/LiteRT model used)
4. F1-score achieved
5. Avg latency in ms
6. peak memory in GB
7. total samples evaluated
8. status: `keep`, `discard`, or `crash`
9. short text description of what this experiment tried

## The experiment loop

LOOP FOREVER:

1. **Observe**: Look at the git state and current `results.tsv`.
2. **Branch**: Ensure you are on a fresh `autoresearch/<tag>` branch from `main`.
3. **Hypothesize**: Tune `triage_sandbox.py` with an experimental idea (e.g., improved system prompt, few-shot examples, or multi-step reasoning).
4. **Commit**: `git commit -am "experiment: <short description>"`
5. **Evaluate**: Run the experiment, passing your hypothesis as the description: 
   `uv run triage_sandbox.py --description "<your hypothesis>" > logs/run.log 2>&1`
6. **Analyze**: Read results: `grep -A 5 "FINAL METRICS" logs/run.log`
7. **Decision**:
   - **IF** F1-score improved AND latency < 4000ms:
     - **Prepare for review**: keep the branch, summarize the change, and open a pull request or handoff note for a human maintainer.
     - **Do not auto-deploy**: a human must approve before the change becomes the default field profile.
   - **ELSE** (Latency too high or F1 dropped):
     - **Discard**: Git reset or delete the experimental branch.
     - **Learn**: Analyze failures in `logs/run.log` and try a different strategy.
8. **Continuation policy**: If the automation platform was configured for recurring work, record the decision and let the next scheduled pulse continue the loop. Do not bypass human review or repository protections.

Always prioritize the 4000ms latency budget and humanitarian safety constraints.
