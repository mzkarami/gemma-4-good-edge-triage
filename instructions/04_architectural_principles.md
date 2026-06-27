# Edge-Triage Architectural Principles

## 1. Shared contracts belong in `edge_triage_core/`

Prompts, labels, runtime defaults, fallback classification, and response shaping that are shared by the CLI, Live API, and sandbox belong in the lightweight core package.

## 2. Product surfaces must not import the research harness

`edge-triage-cli.py` and `live_api.py` must not import `triage_sandbox.py` for normal startup/help. Import-boundary tests should guard this.

## 3. Heavy runtime behavior stays lazy and local

Model loading, `llama_cpp`, artifact bootstrap, CUDA/VRAM probing, and local extraction should happen only in the code paths that need them.

## 4. Thin HTTP boundary, explicit guardrails

`live_api.py` owns HTTP/security controls: upload validation, image sanitization, rate/day limits, concurrency cap, timeout, kill switch, and safe error handling.

## 5. The research sandbox owns benchmarking

`triage_sandbox.py` owns benchmark execution, routing experiments, local data lifecycle, state hashing, and `results.tsv` writes.

## 6. Current vs target architecture must be explicit

Docs must distinguish current implemented behavior from target/future ideas such as mobile/NPU deployments or deeper Paperclip integration.
