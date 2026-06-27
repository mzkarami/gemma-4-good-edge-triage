"""Deterministic humanitarian red-flag escalation for Edge-Triage."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .labels import sanitize_model_text, sanitize_note


@dataclass(frozen=True)
class RedFlag:
    key: str
    pattern: re.Pattern[str]
    reason: str
    forced_label: str = "affected_injured_or_dead_people"


RED_FLAGS = [
    RedFlag("trapped_person", re.compile(r"\b(trapped|pinned|buried|stuck under|cannot get out)\b", re.I), "Possible trapped person requires trained rescue escalation."),
    RedFlag("unconscious_or_not_breathing", re.compile(r"\b(unconscious|not breathing|no pulse|motionless|collapsed person)\b", re.I), "Possible life-threatening casualty cue detected."),
    RedFlag("severe_bleeding", re.compile(r"\b(heavy bleeding|bleeding badly|blood everywhere|severe bleed)\b", re.I), "Severe bleeding cue requires medical/rescue escalation."),
    RedFlag("live_wires", re.compile(r"\b(live wire|downed power|power line|electrocution|electric shock)\b", re.I), "Electrical hazard detected; keep volunteers away and escalate."),
    RedFlag("gas_or_explosion", re.compile(r"\b(gas smell|smell gas|gas leak|explosion|explosive|chemical leak)\b", re.I), "Gas/chemical/explosion hazard detected."),
    RedFlag("structural_collapse", re.compile(r"\b(building collapse|collapsed building|bridge collapse|collapsed bridge|rubble with people)\b", re.I), "Structural collapse cue detected."),
    RedFlag("rising_water", re.compile(r"\b(rising water|flash flood|swept away|children in flood|elderly in flood)\b", re.I), "Fast-moving/rising water cue detected."),
    RedFlag("spreading_fire", re.compile(r"\b(spreading fire|wildfire approaching|people trapped by fire|smoke inhalation)\b", re.I), "Spreading fire or smoke-inhalation cue detected."),
]


def detect_red_flags(*texts: str | None) -> list[dict]:
    haystack = " ".join(sanitize_note(text, max_chars=1200) for text in texts if text)
    flags = []
    for flag in RED_FLAGS:
        if flag.pattern.search(haystack):
            flags.append({"key": flag.key, "reason": flag.reason, "forced_label": flag.forced_label})
    return flags


def apply_red_flag_override(label: str, note: str | None = None, scene_summary: str | None = None, filename: str | None = None) -> tuple[str, list[dict]]:
    flags = detect_red_flags(note, scene_summary, filename)
    if flags and label != "affected_injured_or_dead_people":
        return "affected_injured_or_dead_people", flags
    return label, flags


def red_flag_summary(flags: list[dict]) -> str:
    if not flags:
        return ""
    reasons = "; ".join(sanitize_model_text(flag["reason"], 120) for flag in flags[:3])
    return f"Deterministic red-flag escalation applied: {reasons}"
