# Edge-Triage: Optimized Gemma 4 Models for Disaster Response

This dataset contains optimized model weights for the **Edge-Triage Hybrid Searcher**, a project for the **Gemma 4 Good Hackathon**.

## 📦 Contents
These models have been quantized and optimized for low-latency, multimodal triage in disaster zones.

1.  **Edge-Triage-gemma-4-E4B-it-Q3_K_M.gguf**: Current high-fidelity research model used for the validated full-50 frontier: 0.9794 F1 at 158.61 ms in the Volunteer Speed Profile and 0.9818 F1 at 237.97 ms in the Critical Accuracy Profile.
2.  **Edge-Triage-gemma-4-E4B-it-UD-Q2_K_XL.gguf**: Earlier low-bit edge deployment artifact retained for packaging history and CPU-oriented experiments. Do not cite its older low-score milestone as the current frontier.
3.  **Edge-Triage-mmproj-F16.gguf**: The mandatory multimodal projector for vision tasks.
4.  **Edge-Triage-gemma-4-E2B-it.litertlm**: Official Google AI Edge model for mobile/NPU deployment.

## ⚖️ License
These models are derivative works of the Google Gemma 4 family and are distributed under the **Apache 2.0 License**.

## 🏷️ Branding Compliance
In accordance with the Gemma Model Variant Guidelines:
*   These models are named with the `Edge-Triage-` prefix to distinguish them from official Google releases.
*   **Gemma is a trademark of Google LLC.**

---
*Created for the Gemma 4 Good Hackathon by mzkarami.*
