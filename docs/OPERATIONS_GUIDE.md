# Edge-Triage: Operations Guide for First Responders

**Goal:** Provide actionable, local AI triage on consumer-grade hardware in air-gapped disaster zones.

## 1. Installation
The tool is designed to run on Python 3.11+ with minimal dependencies.

```bash
git clone https://github.com/mzkarami/gemma-4-good-edge-triage.git
cd gemma-4-good-edge-triage
uv sync
```

## 2. Running a Triage
Edge-Triage works with both text reports and photos taken in the field. The field CLI reads shared prompts, labels, and model defaults from `edge_triage_core/`; it does not import the research sandbox just to start or show help. That keeps field startup separate from benchmark bootstrapping, artifact download checks, and CUDA guard logic.

### A. Triage a Text Report
If you only have a verbal or written report:
```bash
uv run edge-triage-cli.py --report "Heavy flooding in Sector 7. Multiple families trapped on roofs."
```

### B. Triage with a Photo (Multimodal)
This is the most powerful mode. The model verifies visual evidence.
```bash
uv run edge-triage-cli.py --image data/images/sample_flood.jpg --report "Flooding reported."
```

### C. Hands-Free Audio Triage (Voice Memo)
If a responder needs to dictate a report while moving:
```bash
uv run edge-triage-cli.py --audio report.wav --image photo.jpg
```
*Note: The system will autonomously transcribe the speech and combine it with the image evidence.*

## 3. Interpreting Results
The tool provides three key outputs:
1.  **[Category]**: The official humanitarian triage label.
2.  **Reasoning**: A 1-sentence explanation of why that label was chosen.
3.  **Field Advice**: Three immediate safety actions based on the specific triage category.

## 4. Troubleshooting
-   **Model Not Found**: Ensure you have downloaded the GGUF models (see `prepare.py`).
-   **High Latency**: The validated field profiles are far below the 4-second response budget, but live local performance depends on model backend, GPU/CPU, and image size. Close other heavy applications and prefer the configured Speed Mode for field sorting.
-   **Image Error**: Ensure the photo path is correct and accessible.
