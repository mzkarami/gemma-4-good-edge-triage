# Edge-Triage: Gemma 4 Multimodal Disaster Response

**Submission for the Gemma 4 Good Hackathon**

## 1. Project Overview

Edge-Triage is a local-first, multimodal disaster-response triage system powered by Gemma 4. It acts as an intelligent field filter: volunteers can classify text/image disaster reports locally, while response leads can inspect an optimization cockpit that shows how the system found its speed/accuracy frontier.

The project is built around a practical constraint: in a disaster zone, cloud connectivity is often unreliable or unavailable. Edge-Triage therefore prioritizes local inference, privacy, and latency that is comfortably below a 4-second field-response budget.

## 2. The Core Idea

Edge-Triage exposes two competition-facing modes:

1. **Volunteer Mode** — the field-facing workflow for high-volume triage.
2. **Optimization Mode** — the research cockpit showing autonomous experiments, keep/discard decisions, and the Pareto frontier.

The Web UI intentionally has only these two judge-facing experiences. The benchmark evidence also reports two validated model profiles: **Volunteer Speed Profile** for volume sorting and **Critical Accuracy Profile** for high-stakes review where a small latency tradeoff is acceptable.

## 3. Current Validated Frontier

Canonical metrics live in [`docs/CURRENT_FRONTIER.md`](CURRENT_FRONTIER.md). Current full-50 MEDIC/QCRI gold-set profiles:

| Profile | Use case | F1 | Accuracy | Latency | Samples | Run |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Volunteer Speed Profile | Default high-volume field sorting | 0.9794 | see run log | 158.61 ms | 50 | EDG-307 r0 / `20260427T200056Z` |
| Critical Accuracy Profile | High-stakes review | 0.9818 | 0.9800 | 237.97 ms | 50 | EDG-480 r2 / `20260515T093558Z` |

Both are far below the 4000 ms mission-critical latency budget.

Important note: EDG-480 is marked `discard` in `results.tsv` because the historical ledger compares against older `1.0000` F1 rows, including at least one row documented as an unrealistic metric artifact. For the hackathon narrative, we compare trustworthy full-50 rows and present the Pareto frontier honestly.

## 4. Autonomous Research Process

We did not only hand-write a prompt. We built an autonomous research workflow around `triage_sandbox.py` and `results.tsv`:

1. Run a candidate routing/prompt/model configuration.
2. Evaluate against the 50-sample MEDIC/QCRI gold set.
3. Record F1, latency, VRAM, state hash, and keep/discard status.
4. Inspect mismatches and target the next narrow ablation.
5. Freeze a field-ready frontier when marginal research gains become less valuable than demo reliability.

Recent EDG-479/EDG-480 ablations showed that the EDG-478 calibrations are complementary and that the final dt5 false positive needs a separate narrow gate:

- `other_dt0` priority recovers `ASONAM2017_38`.
- `none_dt5` priority recovers `ASONAM2017_20`.
- EDG-480's narrow dt5 demotion recovers `ASONAM2017_44`.
- The remaining observed error is a separate unlabelled-dt0 rescue/infrastructure boundary case: `ASONAM2017_8`.

## 5. Technical Innovation

- **Gemma 4 local inference:** GGUF multimodal path through llama.cpp, with LiteRT/Ollama deployment scaffolds.
- **Hybrid routing:** fast metadata/targeted-probe routes are used where reliable; full multimodal review is reserved for harder cases.
- **Pareto-first evaluation:** accuracy and latency are both first-class, because disaster response cannot trade unlimited time for small quality gains.
- **State hashing:** experiment configurations are hashed to avoid duplicate work and keep the research ledger reproducible.
- **Local-first privacy:** sensitive reports can remain on the field device.

## 6. Demo and Judge Experience

The judge-facing curated offline demo lives in `site/` and is designed to work even when hosted inference is unavailable. It is not live inference; it uses fixed public-safe sample cards to demonstrate the volunteer workflow without exposing upload controls or pretending to call the model:

```bash
python3 -m http.server 4173 --directory site
# open http://127.0.0.1:4173
```

It includes:

- Volunteer Mode with clickable curated disaster-report examples, related scenario imagery, triage labels, priority, next action, and latency badges.
- Optional Live Gemma preview using a judge token from the Kaggle submission notes, 25 MB upload cap, rate limits, image metadata stripping, and no upload retention.
- Optimization Mode with the current frontier, EDG-479/EDG-480 ablation decision, and research-ledger framing.
- Evidence sections linking back to `docs/CURRENT_FRONTIER.md`, `results.tsv`, and the public metrics pages.

## 7. Responsible AI and Safety

Edge-Triage avoids giving unsupported medical instructions. It classifies humanitarian reports, highlights urgency, and suggests conservative next actions such as escalating to trained responders, maintaining perimeter safety, or routing supply requests.

The system is intended to support human responders, not replace incident command or medical triage professionals.

Known limitations are stated explicitly in the demo materials: ambiguous or low-context imagery may be misclassified, Live Gemma scene summaries are model-generated and should be verified, and the protected Live Gemma preview is rate-limited so the curated offline demo remains the reliable fallback.

## 8. Compliance and Artifacts

- **Open source:** repository contains code, tests, docs, media assets, and the public metrics ledger.
- **Gemma 4 focus:** project is centered on Gemma 4 local multimodal inference paths.
- **Social good:** addresses disaster response, offline resilience, and privacy-preserving humanitarian triage.
- **Reproducibility:** key metrics are tied to run IDs and state hashes in `results.tsv`.

## 9. Kaggle Visibility Note

The Gemma 4 Good submission requirements describe the Kaggle Writeup as public and require an attached public video, public code repository, and publicly accessible live demo. They also state that any private Kaggle Resource attached to the public Writeup will automatically be made public after the deadline. Therefore, do not treat the submitted Writeup or attached project links as judge-only confidential material.

Operational rule: keep secrets, raw judge tokens, private host details, and unpublished implementation notes out of public Kaggle text and repository files. If a live-preview token is needed, rotate it for the judging window and rely on the static public demo as the durable no-secret fallback.

---

Created by the Edge-Triage swarm for the Gemma 4 Good Hackathon.

Gemma is a trademark of Google LLC.

## Final Submission Links

- Live demo: https://kaggle.nelly.work
- Public repository: https://github.com/mzkarami/gemma-4-good-edge-triage
- Final public video: https://youtu.be/kXVC07Od93E
- Metrics: https://kaggle.nelly.work/metrics.html

