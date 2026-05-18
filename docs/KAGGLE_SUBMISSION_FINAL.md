# Kaggle Submission Final Fields

Use this as the paste-ready source for the public Kaggle submission form/writeup.

## Title

Edge-Triage: Local Disaster Triage When the Cloud Is Gone

## One-line summary

Gemma 4-powered local multimodal triage for messy disaster reports, with a volunteer-facing workflow and a reproducible optimization loop for speed, accuracy, privacy, and human-led safety.

## Public links

- Live demo: https://kaggle.nelly.work
- Volunteer App: https://kaggle.nelly.work/app.html
- Metrics source: https://kaggle.nelly.work/metrics.html
- Roadmap: https://kaggle.nelly.work/roadmap.html
- About the Builder: https://kaggle.nelly.work/about.html
- Public code repository: https://github.com/mzkarami/gemma-4-good-edge-triage
- Video: https://youtu.be/q8sveHsZiCA

## Short project description

Edge-Triage is a local-first disaster-response triage system powered by Gemma 4. A volunteer can enter a short field report, optionally attach a public-safe photo, and receive a humanitarian triage label, priority, explanation, latency context, and a conservative next action. The system is designed for crisis settings where connectivity may be unreliable and sensitive reports should stay close to the field whenever possible.

The public demo has two judge-facing layers. The curated public-safe showcase gives every judge a reliable product experience without requiring model downloads or special hardware. The guarded Live Gemma preview exercises the real upload/API flow through the public site, with rate limits, daily limits, concurrency controls, timeout controls, a kill switch, a 25 MB image cap, server-side image sanitization, text-note limits, and no upload retention.

The project also includes an optimization cockpit and research ledger. Candidate routing/model configurations are evaluated against a 50-sample MEDIC/QCRI gold set, logged in `results.tsv`, and compared on both F1 and latency. Current public metrics are documented in `docs/CURRENT_FRONTIER.md` and shown at https://kaggle.nelly.work/metrics.html.

## Models used

- Unsloth Gemma 4 E4B Instruct GGUF: https://huggingface.co/unsloth/gemma-4-e4b-it-GGUF
  - Primary live/API artifact: `gemma-4-E4B-it-Q3_K_M.gguf`
  - Multimodal projector: `mmproj-F16.gguf`
  - Additional Pareto-search artifact: `gemma-4-E4B-it-UD-Q2_K_XL.gguf`
- Unsloth Gemma 4 E2B Instruct GGUF fallback/bootstrap artifact: https://huggingface.co/unsloth/gemma-4-e2b-it-GGUF
  - `gemma-4-E2B-it-Q4_K_M.gguf`
- LiteRT community Gemma 4 E2B Instruct artifact used for Google AI Edge / LiteRT scaffolding: https://huggingface.co/litert-community/gemma-4-E2B-it-litert-lm
  - `gemma-4-E2B-it.litertlm`

## Responsible AI / safety note

Edge-Triage is decision support, not emergency command. It does not replace trained responders, medical professionals, incident command, or local judgment. Ambiguous or low-context imagery still requires human review. The app avoids unsupported medical instructions and limits model output to bounded triage information: label, priority, explanation, and conservative next action.

## Technical highlights

- Gemma 4-centered local multimodal triage path.
- Volunteer Mode for high-volume field intake.
- Optimization Mode showing the speed/accuracy frontier and keep/discard experiment discipline.
- Current validated profiles:
  - Volunteer Speed Profile: 0.9794 F1, 158.61 ms, full-50 MEDIC/QCRI run EDG-307 r0.
  - Critical Accuracy Profile: 0.9818 F1, 0.9800 accuracy, 237.97 ms, full-50 MEDIC/QCRI run EDG-480 r2.
- Public demo guardrails: HTTPS, localhost-only app/API containers behind reverse proxy, security headers, upload limits, image sanitization, text-note caps, no audio upload in this version, rate limits, concurrency cap, timeout, kill switch, and no upload retention.

## Do not paste into public Kaggle text

- Any `.env` values.
- Private host/IP details.
- Raw upload examples from real people.
- Private operational notes.
- Local-only private repo path.
- Tokens or secrets.
