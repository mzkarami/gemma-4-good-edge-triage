"""Deterministic guidance-basis snippets for Edge-Triage responses."""

from __future__ import annotations

GUIDANCE_BY_LABEL = {
    "affected_injured_or_dead_people": [
        "Route possible casualty or trapped-person reports to trained medical/rescue responders.",
        "Keep bystanders away from secondary hazards such as collapse, fire, water, traffic, or live utilities.",
        "Collect exact location, number of affected people, visible hazards, and access route for human review.",
    ],
    "infrastructure_and_utility_damage": [
        "Keep civilians away from unstable infrastructure, downed utilities, floodwater, gas leaks, and blocked routes.",
        "Route location and access constraints to infrastructure/utility response before sending volunteers closer.",
        "Escalate if damage blocks evacuation, exposes power/gas hazards, or may involve trapped people.",
    ],
    "rescue_volunteering_or_donation_effort": [
        "Coordinate volunteers and supplies through an incident lead before movement into active hazard zones.",
        "Collect requested supply type, drop-off point, coordinator contact, and access conditions.",
        "Avoid convergence that can block responders, evacuation routes, or shelter operations.",
    ],
    "not_humanitarian": [
        "Keep low-confidence or non-disaster reports in human review rather than escalating automatically.",
        "Ask for location, timing, and humanitarian relevance before routing scarce response capacity.",
        "Escalate only if new casualty, infrastructure, evacuation, or responder-support evidence appears.",
    ],
}

RED_FLAG_GUIDANCE = [
    "Red-flag cues override routine routing and require trained-responder review.",
    "Do not ask untrained volunteers to enter unstable, flooded, burning, electrical, or gas-risk areas.",
]


def build_guidance_basis(label: str, red_flags: list[dict] | None = None) -> list[str]:
    guidance = list(GUIDANCE_BY_LABEL.get(label, GUIDANCE_BY_LABEL["not_humanitarian"]))
    if red_flags:
        guidance = RED_FLAG_GUIDANCE + guidance
    return guidance[:5]
