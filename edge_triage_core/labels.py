"""Shared label, parsing, and safe fallback helpers for Edge-Triage."""

from __future__ import annotations

import re

from .prompts import CANONICAL_CATEGORIES

LABEL_METADATA = {
    "affected_injured_or_dead_people": {
        "priority": "Critical human-safety priority",
        "next_action": "Escalate to trained medical/rescue team; avoid moving people unless there is immediate danger.",
        "mode": "Volunteer Mode · Critical Accuracy Profile",
    },
    "infrastructure_and_utility_damage": {
        "priority": "High infrastructure priority",
        "next_action": "Route to infrastructure response; keep civilians away from damaged structures and report coordinates.",
        "mode": "Volunteer Mode · Speed Profile",
    },
    "rescue_volunteering_or_donation_effort": {
        "priority": "Active disaster response / responder activity",
        "next_action": "Route to incident-response coordination; monitor responder safety, containment status, and any nearby evacuation or supply needs.",
        "mode": "Volunteer Mode · Speed Profile",
    },
    "not_humanitarian": {
        "priority": "No disaster triage action",
        "next_action": "Do not escalate; keep in low-priority review queue if context is uncertain.",
        "mode": "Volunteer Mode · Speed Profile",
    },
}


def sanitize_note(note: str | None, max_chars: int = 1000) -> str:
    clean = (note or "").replace("\x00", " ")
    clean = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:max_chars]


def sanitize_model_text(text: str | None, max_chars: int = 220) -> str:
    clean = sanitize_note(text, max_chars=max_chars)
    clean = re.sub(r"(?i)bearer\s+[a-z0-9._~+/=-]+", "[redacted]", clean)
    clean = re.sub(r"(?i)(token|secret|password)\s*[:=]\s*\S+", r"\1=[redacted]", clean)
    clean = clean.replace("file://", "")
    return clean[:max_chars]


def parse_label(raw_text: str) -> str:
    for label in CANONICAL_CATEGORIES:
        if label in raw_text:
            return label
    bracketed = re.search(r"\[([^\]]+)\]", raw_text)
    if bracketed and bracketed.group(1) in CANONICAL_CATEGORIES:
        return bracketed.group(1)
    return "not_humanitarian"


def fallback_classify(note: str, filename: str | None = None) -> str:
    query = f"{filename or ''} {note}".lower()
    if re.search(r"injur|casual|dead|body|medical|rubble|earthquake|trapped|blood|person", query):
        return "affected_injured_or_dead_people"
    if re.search(r"fire|wildfire|forest fire|smoke|burn|flame|firefighter|responder|rescue|evacuat", query):
        return "rescue_volunteering_or_donation_effort"
    if re.search(r"bridge|road|flood|utility|power|damage|collapsed|infrastructure", query):
        return "infrastructure_and_utility_damage"
    if re.search(r"donat|volunteer|supply|water|blanket|shelter|food|logistic", query):
        return "rescue_volunteering_or_donation_effort"
    return "not_humanitarian"


def fallback_scene_summary(label: str, note: str, filename: str | None = None) -> str:
    hints = []
    if note:
        hints.append(f"field note says: {sanitize_model_text(note, 140)}")
    if filename:
        hints.append(f"filename: {sanitize_model_text(filename, 80)}")
    evidence = "; ".join(hints) or "no field note or filename clues were supplied"
    return f"Guarded fallback used text metadata only ({evidence}); live visual Gemma was not active."
