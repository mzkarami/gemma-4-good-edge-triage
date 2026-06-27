# Edge-Triage Coding Guidelines

## 1. Prefer small, measured slices

Make narrow changes with clear verification. Avoid broad rewrites when a boundary extraction, helper, or test can solve the problem.

## 2. Preserve public/private boundaries

Before staging files, check for generated images, local shards, `.env`, credentials, private notes, local IDE metadata, and model artifacts.

## 3. Keep imports intentional

Core modules should stay side-effect free. CLI and API paths should defer heavy dependencies until needed.

## 4. Tests before behavior changes

Import boundaries, response schemas, upload guardrails, and benchmark invariants should have tests before or alongside implementation changes.

## 5. Commit focused changes

Keep docs, tests, workflow, and runtime changes focused enough that reviewers can understand the risk.
