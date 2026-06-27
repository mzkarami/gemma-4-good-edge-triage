# Edge-Triage Product Principles

## 1. Human command stays human

Edge-Triage routes, explains, and prioritizes. It does not command responders, diagnose patients, or replace trained incident leadership.

## 2. Fast when volume is high, careful when stakes are high

The product supports a speed profile for high-volume sorting and a critical accuracy profile for ambiguous or high-stakes review. Public copy must explain when each profile is appropriate.

## 3. Curated demo and live inference are different products

The curated offline demo is the reliable public judging path. The optional Live Gemma preview is an extra bounded path that may fail closed without breaking the demo.

## 4. Public claims require evidence

Benchmark claims must trace to `docs/CURRENT_FRONTIER.md`, `results.tsv`, validation reports, or public research logs. Historical milestones should be labeled historical.

## 5. Plain responder language

Prefer direct operational language: report, scene, category, priority, next action, responder, route, verify, escalate. Avoid hype and unsupported autonomy framing.

## 6. Local-first is a design pressure

The project should keep sensitive field data local where practical and make cloud/live paths optional, guarded, and clearly labeled.
