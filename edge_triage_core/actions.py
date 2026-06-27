"""Responder action-pack helpers for Edge-Triage."""

from __future__ import annotations

ACTION_PACKS = {
    "affected_injured_or_dead_people": {
        "safe_next_action": "Escalate to trained medical/rescue responders and keep bystanders away from secondary hazards.",
        "do_not_do": "Do not move injured people unless there is immediate danger such as fire, collapse, or rising water.",
        "collect_next": ["exact location", "number of people affected", "visible hazards", "access route", "responder already on scene"],
        "escalate_if": ["unconscious or not breathing", "trapped person", "heavy bleeding", "fire or structural instability nearby"],
        "route_to": "medical/rescue coordination",
    },
    "infrastructure_and_utility_damage": {
        "safe_next_action": "Mark the area unsafe, keep civilians back, and route coordinates to infrastructure/utility response.",
        "do_not_do": "Do not ask volunteers to inspect unstable bridges, roads, buildings, gas leaks, or power lines directly.",
        "collect_next": ["coordinates or landmark", "blocked route", "utility hazard", "water level", "people nearby"],
        "escalate_if": ["people trapped", "live wires", "gas smell", "bridge/building instability", "road blocks evacuation"],
        "route_to": "infrastructure and utility response",
    },
    "rescue_volunteering_or_donation_effort": {
        "safe_next_action": "Route to incident-response coordination and verify what help is needed before sending more volunteers or supplies.",
        "do_not_do": "Do not self-deploy unrequested volunteers or supplies into an active hazard zone.",
        "collect_next": ["requested supply type", "drop-off point", "coordinator contact", "access conditions", "responder safety status"],
        "escalate_if": ["responders are overwhelmed", "evacuation is active", "shelter/supply shortage", "unsafe volunteer convergence"],
        "route_to": "incident logistics coordination",
    },
    "not_humanitarian": {
        "safe_next_action": "Keep in low-priority review unless new disaster context appears.",
        "do_not_do": "Do not escalate as disaster response without human review or additional context.",
        "collect_next": ["why it was submitted", "location context", "time sensitivity", "humanitarian relevance"],
        "escalate_if": ["new casualty cue", "new infrastructure damage cue", "new active evacuation/rescue cue"],
        "route_to": "low-priority review queue",
    },
}


def build_action_pack(label: str) -> dict:
    return dict(ACTION_PACKS.get(label, ACTION_PACKS["not_humanitarian"]))
