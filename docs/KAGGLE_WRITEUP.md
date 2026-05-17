# Edge-Triage: Local Disaster Triage When the Cloud Is Gone

**Submission:** Gemma 4 Good Hackathon
**Category:** Global Resilience / Disaster Response
**Core idea:** Gemma 4-powered local multimodal triage for disaster reports, with a human-led volunteer workflow and a reproducible self-learning optimization loop.

> Link placeholders to fill at submission time:
> - Live demo: `https://kaggle.nelly.work`
> - Code repository: `https://github.com/mzkarami/Gemma-4-Edge-Triage`
> - Video: `[PUBLIC_VIDEO_URL]`

## 1. Plain-English Summary

During floods, wildfires, earthquakes, and hurricanes, responders receive messy reports from many sources: short text messages, photos, voice notes, social posts, and volunteer observations. Connectivity may be unreliable exactly when the report volume is highest.

Edge-Triage is a local-first disaster triage system powered by Gemma 4. A volunteer enters a short report, optionally with a photo, and the app returns a humanitarian triage label, priority, confidence context, latency, and a conservative next action. The responder stays in control: Edge-Triage routes and explains; it does not replace incident command, medical professionals, or local judgment.

The same project also gives data science and response teams a repeatable way to improve the system. New disaster examples can be evaluated against a gold set, experiments are logged in `results.tsv`, and only useful speed/accuracy improvements are promoted into the public frontier.

That split is the product: simple for volunteers, measurable for researchers.

## 2. Why Gemma 4 Matters Here

Gemma 4 is useful for humanitarian response because it can bring multimodal reasoning closer to the field. Edge-Triage is designed around a local Gemma 4 path where short field notes and image context can be processed near the incident instead of depending on a cloud service that may be unavailable or inappropriate for sensitive reports.

The project centers on:

- **Local multimodal triage:** text and photos can stay close to the field device.
- **Fast response:** the validated profiles run far below a 4-second field-response budget.
- **Privacy-aware design:** disaster reports do not need to be uploaded to a general cloud model for basic routing.
- **Practical deployment paths:** the repository includes GGUF / llama.cpp-centered local inference, plus Ollama and LiteRT / Google AI Edge-oriented scaffolding.
- **Human-led outputs:** the model provides label, priority, explanation, and conservative next action, not command authority.

## 3. Judge-Facing Demo

The public Web UI has two main experiences.

### Volunteer Mode

Volunteer Mode is the field-facing workflow. Judges can click curated public-safe disaster scenarios and see how Edge-Triage updates the report image, label, priority, latency badge, explanation, and safe next action.

The curated offline demo is intentionally honest: it is a fixed public-safe fallback and is not presented as live inference. It exists so every judge can evaluate the product experience even if a protected model endpoint is unavailable.

There is also an optional **Live Gemma preview** path for the real upload/API flow. It is token-gated, rate-limited, uses a 25 MB image cap, strips image metadata, and does not retain uploads.

### Optimization Mode

Optimization Mode is the research cockpit. It shows how Edge-Triage improves itself over time:

```text
New crisis examples
      ↓
Gemma 4 candidate profile
      ↓
Gold-set evaluation
      ↓
F1 + latency + safety check
      ↓
Keep or discard
```

Instead of presenting a single magic prompt, the project exposes the speed/accuracy frontier and the keep/discard reasoning behind recent experiments. This helps ML, AI, and agents-oriented judges inspect whether the system is actually improving in a controlled way.

## 4. Current Validated Frontier

The canonical source of truth is [`docs/CURRENT_FRONTIER.md`](docs/CURRENT_FRONTIER.md). Public claims in the README, site, video, and writeup should stay aligned with that file.

| Profile | Use case | F1 | Accuracy | Latency | Samples | Run |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Volunteer Speed Profile | High-volume field sorting | 0.9794 | see run log | 158.61 ms | 50 | EDG-307 r0 / `20260427T200056Z` |
| Critical Accuracy Profile | High-stakes review | 0.9818 | 0.9800 | 237.97 ms | 50 | EDG-480 r2 / `20260515T093558Z` |

Both profiles are far below the 4,000 ms disaster-response budget. We present them as a frontier rather than pretending one configuration is universally best. A volunteer intake queue needs speed; an incident lead reviewing ambiguous possible-casualty or blocked-route cases may choose the slightly slower high-confidence profile.

Important metric note: `results.tsv` is an experiment ledger, not a leaderboard. It includes diagnostic rows, low-VRAM guard runs, and historical artifact rows. For public reporting we use trustworthy comparable full-50 rows documented in `docs/CURRENT_FRONTIER.md`, not raw maxima from the ledger.

## 5. What Is Technically Interesting

Edge-Triage combines a practical field UI with an autonomous research loop.

- **Local Gemma 4 inference:** multimodal disaster reports can be processed on edge-oriented infrastructure rather than requiring cloud connectivity.
- **Hybrid routing:** easy cases can use faster routes while harder cases can escalate to fuller multimodal review.
- **Pareto-first evaluation:** accuracy, latency, and operational safety are all first-class because disaster response cannot trade unlimited time for small metric gains.
- **State-hashed experimentation:** experiment states are logged so duplicate work and confusing historical rows can be identified.
- **Keep/discard discipline:** candidate changes are evaluated against the 50-sample MEDIC/QCRI gold set before they are treated as public profiles.

Recent EDG-479 / EDG-480 ablations showed why this matters. Individual calibrations did not stand alone, but combined calibrations plus a narrow dt5 demotion produced the current Critical Accuracy Profile candidate: `0.9818 F1 / 237.97 ms` on the full 50-sample gold set.

## 6. Responsible AI and Safety

Edge-Triage is decision support, not emergency command.

The app classifies humanitarian reports, highlights urgency, and suggests conservative next actions such as escalation, perimeter safety, or supply routing. It avoids unsupported medical instructions and does not delegate medical or incident-command authority to the model.

Known limitations are stated in the demo:

- Ambiguous or low-context images still require human review.
- Live Gemma scene summaries are model-generated and should be verified.
- The protected live preview is rate-limited and token-gated.
- The curated offline demo remains the reliable public fallback.

This is also why the project is local-first. In humanitarian settings, privacy and infrastructure resilience matter as much as raw model quality.

## 7. Evidence and Reproducibility

The demo evidence connects the product story to measured runs, public-safe scenarios, and reproducible documentation.

Key files:

- `site/` — judge-facing demo with Volunteer Mode, Optimization Mode, Evidence, Roadmap, and About pages.
- `site/metrics.html` — human-readable metrics source explaining the frontier and why raw ledger maxima are filtered.
- `docs/CURRENT_FRONTIER.md` — canonical competition-facing metric source.
- `results.tsv` — experiment ledger with F1, latency, VRAM, state hashes, and keep/discard status.
- `triage_sandbox.py` — evaluation and optimization harness.
- `live_api.py` — optional token-gated Live Gemma preview path.
- `media/` — public-safe screenshots, cover image, scenario media, and capture manifest.
- `tests/` — regression checks for site content, live API behavior, routing, evaluation, and safety-related UX.

## 8. Roadmap

The hackathon demo proves the core idea. The next four product extensions would make it more deployable for real response teams:

1. **Native mobile UI:** Android and iOS interfaces with offline caching, camera capture, location-safe metadata, and send-to-command handoff when connectivity returns.
2. **Trusted humanitarian guidance library:** source-linked instructions from organizations such as the UN, WHO, IFRC/Red Cross, and local emergency agencies.
3. **Low-bandwidth inclusion:** multilingual, voice, and SMS-friendly workflows for volunteers who may not have stable data access.
4. **NGO deployment kit:** training playbooks, governance templates, label adaptation, tabletop drills, and anonymized improvement cases that can feed back into the self-learning evaluation loop.

## 9. Motivation

This project is shaped by lived humanitarian context. The builder has lived with displacement from a very young age, spent years close to war-area realities, and later worked through Data and AI efforts with an NGO helping other NGOs pro-bono.

That experience makes the problem feel concrete. In crisis situations, systems break, information becomes fragmented, and people under pressure need tools that are practical, respectful, and safe. Many humanitarian teams do not need flashy AI; they need systems that protect sensitive information, explain their outputs, work with limited connectivity, and help them use limited time better.

Edge-Triage is a small prototype in that direction: conservative, auditable decision support for people already doing the hard work.

## 10. Submission Links

- Live demo: `https://kaggle.nelly.work`
- Code repository: `https://github.com/mzkarami/Gemma-4-Edge-Triage`
- Video: `[PUBLIC_VIDEO_URL]`
- Metrics source: `https://kaggle.nelly.work/metrics.html`
- Roadmap: `https://kaggle.nelly.work/roadmap.html`
- About the Builder: `https://kaggle.nelly.work/about.html`

Gemma is a trademark of Google LLC.
