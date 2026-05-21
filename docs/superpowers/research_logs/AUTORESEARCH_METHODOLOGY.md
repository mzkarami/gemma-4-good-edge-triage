# Auto Research Methodology: In-Context Optimization

This document explains the technical methodology used in the Edge-Triage project. It is intended for developers and researchers joining the Gemma 4 Good Hackathon swarm.

## 1. "Research" vs. "Training"
Unlike traditional machine learning which modifies model weights (Training/Fine-Tuning), this project focuses on **In-Context Research (ICR)**.

*   **Static Weights:** We use a frozen Gemma 4 GGUF model. No internal parameters are changed.
*   **Search Space:** The "Agent Researcher" searches for the optimal **Prompt Architecture** and **Inference Parameters** (quantization, context length).
*   **Speed:** Because we don't calculate gradients or update weights, an "Experiment" takes minutes rather than hours, allowing for ~100 iterations per night.

## 2. The Feedback Loop
The system automates the Scientific Method using three core components:

1.  **Ground Truth (`prepare.py`):** Fixed evaluation logic using real-world disaster data (**CrisisMMD**). It measures F1-Score (accuracy) and Latency (speed).
2.  **The Sandbox (`triage_sandbox.py`):** The mutable experimental code. The agent hacks this file to try new strategies (e.g., Few-Shot, Chain of Thought).
3.  **The Researcher Agent (`program.md`):** An LLM instructed to analyze previous failures and propose code changes to improve metrics.

## 3. Data Integrity
*   **Source:** We use the **QCRI/CrisisMMD** dataset, containing thousands of real-world disaster reports (images + text).
*   **Human-in-the-loop Labels:** The "Ground Truth" consists of manual annotations by disaster response experts.
*   **Evaluation:** We use a representative "Gold Set" of 100 samples to ensure fast, reliable benchmarking.

## 4. Current Strategies
*   **Iteration 0 (Baseline):** Simple zero-shot instruction. (F1: 0.0689)
*   **Iteration 1 (Few-Shot):** Adding 3 concrete examples to anchor the model's output format. (F1: 0.3092)
*   **Iteration 2 (Chain of Thought):** Encouraging step-by-step reasoning to improve complex triage logic. (In Progress)
