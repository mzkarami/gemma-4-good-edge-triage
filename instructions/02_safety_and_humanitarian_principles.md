# Safety and Humanitarian Principles

## 1. Decision support only

Every user-facing path must preserve the boundary: Edge-Triage is decision support for disaster-response triage, not emergency authority, medical advice, or a replacement for trained responders.

## 2. Constrained categories

Outputs should stay inside the canonical humanitarian categories unless a documented product decision expands them:

- `affected_injured_or_dead_people`
- `infrastructure_and_utility_damage`
- `rescue_volunteering_or_donation_effort`
- `not_humanitarian`

## 3. Conservative next actions

Next actions should route attention and encourage verification. They should not prescribe medical treatment or unsafe physical action.

## 4. Ambiguity must remain visible

Ambiguous, low-context, or model-fallback cases should not be presented as certain. The UI/API should make curated-vs-live and fallback-vs-model behavior explicit.

## 5. Safety guardrails should be deterministic where possible

Upload limits, MIME checks, timeout bounds, rate limits, concurrency caps, and output schemas should be enforced by code, not only by model instructions.
