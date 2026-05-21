# Research Log: Task 5 - Latency Optimization (< 4s)

**Date:** April 15, 2026
**Status:** In Progress
**Target:** Reduce multimodal inference latency from ~6.2s to < 4.0s.

## 1. Problem Statement
The current multimodal triage pipeline achieves a strong F1-score (0.63-0.66) but exceeds the field-operation latency budget. For volunteers in disaster zones, a 6-second wait per image is too slow for high-volume sorting.

## 2. Optimization Strategy
We are implementing a "Production-Grade Edge Optimization" suite:

1.  **Prefix Caching:** Enable `llama-cpp` KV-caching for the static system prompt and few-shot examples.
2.  **Prompt Compression:** Reducing the system prompt token count by ~30% through surgical editing.
3.  **Vision Tuning:** Optimizing `n_batch` and `n_ctx` specifically for the Llava vision projector.
4.  **Conditional Reasoning:** Implementing a "Fast-Path" for high-confidence non-humanitarian scenes to skip reasoning tokens.

## 3. Implementation Plan
- [ ] **Step 1: Diagnostic Instrumentation.** Modify `triage_sandbox.py` to track TTFT (Time-to-First-Token) and TPS (Tokens-Per-Second).
- [ ] **Step 2: Baseline Performance Audit.** Run a 50-sample benchmark with instrumentation to identify if the bottleneck is ingestion or generation.
- [ ] **Step 3: KV-Cache Implementation.** Enable persistent context in the sandbox.
- [ ] **Step 4: Prompt Compaction.** Rewrite the `TRIAGE_SYSTEM_PROMPT` for efficiency.
- [ ] **Step 5: Final Pareto Verification.** Ensure F1-score remains > 0.60 while latency drops < 4s.

## 4. Diagnostic Run Findings (Apr 15)
- **Samples:** 5
- **Avg TTFT:** 1589 ms
- **Avg Latency (10 tokens):** 1859 ms
- **Generation Speed:** ~32.4 tokens/sec
- **Prefix Matching:** Active (`Llama.generate: 523 prefix-match hit`).

### Analysis:
1.  **Vision Bottleneck:** Despite a text prefix hit, the Time-to-First-Token (TTFT) remains high (~1.5s). This is likely due to the ~576 vision tokens that must be processed for every unique image.
2.  **Token Budget:** At 32 TPS, we can generate a maximum of ~80 tokens to stay within the 4.0s budget (1.5s TTFT + 2.5s generation). Our current "Field Advice" goal of 300 tokens is mathematically impossible at the current precision (Q3_K_M).
3.  **Strategy Pivot:** 
    *   Test **Q2_K** or **IQ2_M** quantization to increase TPS.
    *   Implement **Conditional Reasoning**: Only generate advice for high-stakes categories.
    *   Compress "Field Advice" to 3 bullet points (max 60 tokens).
