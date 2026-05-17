# Edge-Triage 3-Minute Demo Video Script

Target length: 2:45-3:00
Tone: confident, practical, humanitarian, demo-first, technical enough for Kaggle judges
Primary URL to show: https://kaggle.nelly.work
Public video style: clean title card + screen recording + voiceover + a few static screenshot cuts

## Reference scan: Kaggle winner video/writeup cues

Reference reviewed: Gemma Vision, winner of the Gemma 3n Impact Challenge / Gemma 4 Good writeup reference.

Useful lessons for our video:
- Open with a clear title card and one-line promise before any raw browser/terminal footage.
- A short disaster-context montage can work well, but keep it respectful: 3-5 seconds total, no graphic injury, no sensational music, no exploitative imagery.
- Use public-domain or clearly licensed footage/stills only, with credits captured in the writeup or end card.
- Lead with the human problem, then show the product quickly. Do not spend the first minute on architecture.
- Keep the mood polished but not cinematic: clean, direct, credible, mission-driven.
- Make the first demo example obvious to a judge watching in a small embedded player.
- Show usability decisions and real-world constraints, not only model scores.
- Explain implementation depth through concrete evidence: local-first intent, privacy, latency, evaluation harness, and edge-case handling.
- End with impact and links, not a long technical appendix.
- Avoid overclaiming. The strongest tone is "practical field decision support," not "AI replaces responders."

## Core message

Edge-Triage is a local-first Gemma 4 disaster triage system. It gives volunteers a simple field workflow and gives response/data teams a measurable optimization loop. The public demo should feel like a winning Kaggle demo: immediate problem, visible workflow, concrete proof, and responsible human-led framing.

## Final narration draft, target 2:15-2:35 raw OBS recording

This is Edge-Triage: local disaster triage when the cloud is gone.

In the first hours after a flood, earthquake, wildfire, or hurricane, people on the ground are trying to answer simple but urgent questions: What happened here? How serious is it? Who needs to see this first? And what should we do next without making things worse?

But disasters do not wait for perfect conditions. Networks fail. Reports arrive as messy images, text reports, and audio notes. Volunteers may be scared, tired, and moving fast. In those moments, useful technology is the kind that helps people make a careful first decision.

Edge-Triage is built for that moment. A volunteer can open a simple workflow, choose a report, and get back a clear category, priority, explanation, and conservative next action. It does not replace responders, doctors, or incident command. It helps route the right information to the right people sooner.

Here in Volunteer Mode, I am using public-safe scenarios so judges can always try the experience. This damaged infrastructure report becomes something a field team can act on: a clear category, high priority, and guidance to keep people away from unsafe structures while escalating to the right response team.

The goal is to reduce confusion. If many volunteers send reports at once, Edge-Triage helps create order: what is blocked, what is dangerous, what can wait, and what needs human review now.

There is also a protected Live Gemma preview for judges. It is guarded with token access, rate limits, upload caps, metadata stripping, and no upload retention. The judge token is in the submission description, so judges can test image classification directly without running the repository locally. Disaster images can be sensitive, so privacy and safety are part of the product, not an afterthought.

Optimization Mode is the self-improving loop behind the app. It tests configurations, compares results, and helps the system get better over time instead of staying as a one-off demo. The exact benchmark numbers are on the site and in the repository, but the important point is simple: this is designed to learn from measurement.

That matters because trust in disaster response comes from clarity. A volunteer should understand the result. A coordinator should understand why a report was prioritized. And a researcher should be able to see how the system was tested and where it can improve.

Edge-Triage is powered by Gemma and designed around a human boundary: the model helps with the first pass, but people stay responsible for high-stakes decisions. The codebase also includes Google AI Edge and LiteRT scaffolding, so the same direction supports both native on-device deployment and the guarded cloud preview.

The live demo is available at kaggle.nelly.work.

## Recommended structure

### 0:00-0:12 — Title card / promise

Visual:
- Start on `media/brand/edge-triage-cover-1600x900.jpg`.
- Use large, high-contrast text. Do not start on a terminal or messy browser tab.

Voiceover:
This is Edge-Triage: local disaster triage when the cloud is gone.

On-screen text:
Local disaster triage when the cloud is gone
Gemma 4 Good Hackathon

### 0:12-0:30 — Problem / why it matters

Visual:
- Cut from title card to live site hero at `https://kaggle.nelly.work`.
- Slowly move to the hero section.

Voiceover:
During floods, wildfires, earthquakes, and hurricanes, responders receive messy reports from everywhere: photos, short notes, social posts, and volunteer observations. But the moment report volume spikes is often the same moment connectivity becomes unreliable.

On-screen text:
Messy field reports
Unreliable connectivity
Privacy-sensitive images

### 0:30-0:48 — What Edge-Triage is

Visual:
- Show the homepage hero and the two-mode framing.
- Briefly show Volunteer Mode and Optimization Mode navigation/sections.

Voiceover:
Edge-Triage is a local-first multimodal triage system powered by Gemma 4. A volunteer can submit a short report, optionally with a photo, and the system returns a humanitarian label, a priority, a short explanation, latency, and a conservative next action.

It is not replacing incident command or medical professionals. It is decision support for routing, prioritizing, and explaining reports under pressure.

On-screen text:
Volunteer workflow + measurable research loop
Human-led decision support

### 0:48-1:22 — Volunteer Mode walkthrough

Visual:
- Open Volunteer Mode.
- Click a curated scenario card, ideally bridge/flood or damaged infrastructure.
- Show the image, label, priority, next action, and analysis panel.
- Use `media/screenshots/02-volunteer-mode.png` if a clean prerecorded segment is easier.

Voiceover:
This is Volunteer Mode. I start with curated public-safe scenarios so judges can always evaluate the product experience, even if a live model endpoint is unavailable.

In this example, a damaged bridge report is classified as infrastructure and utility damage. The output is deliberately simple: high infrastructure priority, a short explanation, and a conservative next action to route the report while keeping civilians away from damaged structures.

The point is speed and clarity: help a volunteer sort the report, preserve human control, and avoid giving unsupported medical or command instructions.

On-screen text:
Label: infrastructure and utility damage
Priority: high infrastructure priority
Action: route to response team

### 1:22-1:48 — Live Gemma preview / guarded API

Visual:
- Show the Live Gemma preview UI, but do not reveal the judge token.
- If recording manually, paste token off-screen or use an already captured live result screenshot.
- Show `media/screenshots/05-live-result-card.png` or one of:
  - `media/screenshots/06-live-optimization-bridge-flood.png`
  - `media/screenshots/07-live-optimization-relief-supplies.png`
  - `media/screenshots/08-live-optimization-evacuation-assistance.png`

Voiceover:
For judges, there is also a protected Live Gemma preview. It is token-gated, rate-limited, caps uploads at 25 megabytes, strips image metadata, and does not retain uploads.

The live path uses the current Gemma 4 GGUF model with the multimodal projector. The static demo remains the reliable public fallback, while the guarded API shows the real upload flow when the judge token is provided.

On-screen text:
Live API: token-gated
Uploads capped, sanitized, not retained
Static demo remains available

### 1:48-2:22 — Optimization Mode / why this is more than a prompt

Visual:
- Switch to Optimization Mode.
- Show frontier metrics and research loop.
- Show `media/screenshots/03-optimization-mode.png` and `media/screenshots/04-metrics-page.png`.
- Optional cut to `media/charts/research-progress.png`.

Voiceover:
Edge-Triage is not just a hand-written prompt. The project includes an autonomous evaluation harness around a 50-sample MEDIC/QCRI-style gold set.

Candidate configurations are tested, logged, and either kept or discarded based on F1, latency, safety, and reproducibility. The public demo exposes that process instead of hiding it.

The current frontier has two validated profiles: a Volunteer Speed Profile at 0.9794 F1 and 158.61 milliseconds, and a Critical Accuracy Profile candidate at 0.9818 F1, 0.9800 accuracy, and 237.97 milliseconds. Both are far below a 4-second disaster-response budget.

On-screen text:
Speed Profile: 0.9794 F1 / 158.61 ms
Accuracy Profile: 0.9818 F1 / 237.97 ms
Both below 4-second field budget

### 2:22-2:42 — Responsible AI / privacy / local-first value

Visual:
- Show safety copy or About/Roadmap page.
- Optional show app disclaimer text.
- Keep visuals calm and credible, not hype-heavy.

Voiceover:
This matters because disaster response is not only an accuracy problem. It is also a privacy, reliability, and operational safety problem.

Edge-Triage is designed so sensitive reports can stay close to the field device. Outputs are constrained to triage labels, explanations, and conservative next actions. Ambiguous or high-stakes cases still require human review.

On-screen text:
Privacy-aware
Human-led
Conservative next actions

### 2:42-2:56 — Evidence and links

Visual:
- Show the live URL, metrics page, and GitHub repository.
- Show `docs/CURRENT_FRONTIER.md` or metrics page briefly.

Voiceover:
The live demo is available at kaggle.nelly.work. The repository includes the demo site, the guarded API, the evaluation harness, tests, deployment docs, model-preparation scripts, media assets, and the public metric source.

Gemma 4 gives the project its local multimodal reasoning path. Edge-Triage wraps that in a workflow responders could actually understand, test, and improve.

On-screen text:
Live demo: kaggle.nelly.work
Code: github.com/mzkarami/Gemma-4-Edge-Triage
Metrics: kaggle.nelly.work/metrics.html

### 2:56-3:00 — Closing

Visual:
- Return to hero/cover image.

Voiceover:
Edge-Triage is local disaster triage when the cloud is gone: simple for volunteers, measurable for researchers, and careful about human responsibility.

On-screen text:
Edge-Triage
Local disaster triage when the cloud is gone

## Shorter fallback script, if we need 90 seconds

Edge-Triage is a local-first disaster triage system powered by Gemma 4. During floods, wildfires, earthquakes, and hurricanes, responders receive messy reports from photos, short notes, social posts, and volunteers, often when connectivity is unreliable.

In Volunteer Mode, a field user can review a report and image, then receive a humanitarian label, priority, explanation, latency, and conservative next action. The responder stays in control. Edge-Triage routes and explains; it does not replace incident command or medical professionals.

The public demo includes curated public-safe scenarios so judges can always test the product experience. It also includes a protected Live Gemma preview using a token-gated API with upload caps, metadata stripping, rate limits, and no upload retention.

Optimization Mode shows the research loop behind the system. Candidate configurations are evaluated against a 50-sample gold set and logged by F1, latency, and keep/discard status. The current frontier includes a Volunteer Speed Profile at 0.9794 F1 and 158.61 milliseconds, and a Critical Accuracy Profile candidate at 0.9818 F1 and 237.97 milliseconds. Both are far below a 4-second field-response budget.

The live demo is at kaggle.nelly.work, with metrics, roadmap, and repository links included. Edge-Triage is local disaster triage when the cloud is gone: simple for volunteers, measurable for researchers, and careful about human responsibility.

## Recording checklist

Before recording:
- Open `https://kaggle.nelly.work` in a clean browser window.
- Browser zoom: 90% or 100%, whichever fits the hero and cards cleanly.
- Hide bookmarks, notifications, terminal windows, and secrets.
- Do not show the judge token. If using live mode, paste it off-screen or use the checked-in live-result screenshots.
- Keep mouse movement slow and deliberate.
- Use 1080p or 1440p screen capture.

Suggested shots:
1. Hero / live URL.
2. Volunteer Mode scenario card click.
3. Result card close-up.
4. Live Gemma preview screenshot/result.
5. Optimization Mode frontier.
6. Metrics page.
7. GitHub/docs evidence.
8. Closing hero.

Public-safety rules:
- No `.env` files.
- No raw judge token.
- No server IP/admin panels.
- No terminal command history with secrets.
- No private Kaggle notes.

## Notes for final edit

- Keep the voiceover under 420 words for a comfortable 3-minute pace.
- If the video feels rushed, remove one live-result example before cutting the optimization metrics.
- The three claims that must stay exactly aligned with docs:
  - Speed Profile: 0.9794 F1 / 158.61 ms.
  - Critical Accuracy Profile: 0.9818 F1 / 0.9800 accuracy / 237.97 ms.
  - Both are below the 4-second field-response budget.
