# Edge-Triage Instructions

This directory is the team and agent operating layer for Edge-Triage. It is inspired by the ILUMAE instruction pattern, adapted for a public local-first disaster triage project with a research benchmark loop and strict humanitarian safety boundaries.

Use these docs before changing product behavior, architecture, runtime, prompts, evaluation, deployment, public claims, or tests.

## Canonical instruction set

1. [Project overview and vision](00_project_overview_and_vision.md)
2. [Product principles](01_product_principles.md)
3. [Safety and humanitarian principles](02_safety_and_humanitarian_principles.md)
4. [Privacy and data principles](03_privacy_and_data_principles.md)
5. [Architectural principles](04_architectural_principles.md)
6. [Research and evaluation principles](05_research_and_evaluation_principles.md)
7. [Coding guidelines](06_coding_guidelines.md)
8. [Testing strategy](07_testing_strategy.md)
9. [DevOps and deployment](08_devops_and_deployment.md)
10. [AI agent workflow](09_ai_agent_workflow.md)
11. [Coding agent acceptance gate](10_coding_agent_acceptance_gate.md)

## How to use this directory

- Product changes start with product and humanitarian safety principles.
- Architecture changes start with `docs/architecture/README.md`, runtime-boundary docs, and ADRs.
- Evaluation or public metric changes start with `docs/CURRENT_FRONTIER.md`, `results.tsv`, and `docs/testing/`.
- Deployment changes start with `08_devops_and_deployment.md` and `docs/operations/`.
- Agent work follows `09_ai_agent_workflow.md` and `10_coding_agent_acceptance_gate.md`.

## Rule of precedence

When documents disagree:

1. User instruction in the current task wins.
2. Safety, privacy, and security requirements win over convenience.
3. `instructions/`, `docs/README.md`, and `docs/architecture/` are canonical for current work.
4. `docs/CURRENT_FRONTIER.md` is canonical for public benchmark claims.
5. Historical research logs and old submission drafts are reference unless a current doc promotes them.
