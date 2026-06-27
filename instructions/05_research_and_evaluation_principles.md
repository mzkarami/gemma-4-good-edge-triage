# Research and Evaluation Principles

## 1. Benchmark claims need traceability

Public metrics must trace to `docs/CURRENT_FRONTIER.md`, `results.tsv`, run logs, and validation reports. Do not update public copy from memory or isolated anecdotes.

## 2. Keep/discard is evidence-based

A research change should be kept only when it improves the desired frontier without breaking safety, latency, or comparability gates.

## 3. State hashes matter

Prompt, model, data, image payload, and runtime knobs that affect predictions should be represented in the state hash or documented as non-comparable.

## 4. Non-comparable runs must be labeled

CPU fallback, missing CUDA, reduced GPU layers, missing telemetry, partial samples, or diagnostic runs must not be mixed into frontier claims as if they were comparable full-profile runs.

## 5. Research logs are audit trail

EDG logs are valuable historical evidence. Current public claims still flow through the current frontier doc and validation reports.
