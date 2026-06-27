"""Shared response-building helpers for Edge-Triage."""

from __future__ import annotations

from .actions import build_action_pack
from .guidance import build_guidance_basis
from .labels import LABEL_METADATA, sanitize_model_text
from .language import build_radio_script, normalize_language, normalize_output_format
from .safety import apply_red_flag_override, red_flag_summary


def build_triage_response(
    label: str,
    latency_ms: float,
    live: bool,
    scene_summary: str,
    *,
    note: str | None = None,
    filename: str | None = None,
    language: str | None = None,
    output_format: str | None = None,
) -> dict:
    clean_summary = sanitize_model_text(scene_summary)
    final_label, red_flags = apply_red_flag_override(label, note=note, scene_summary=clean_summary, filename=filename)
    meta = LABEL_METADATA[final_label]
    action_pack = build_action_pack(final_label)
    language_code = normalize_language(language)
    format_code = normalize_output_format(output_format)
    response = {
        "label": final_label,
        "original_label": label,
        "priority": meta["priority"],
        "next_action": action_pack["safe_next_action"],
        "latency_ms": round(latency_ms, 2),
        "mode": meta["mode"],
        "scene_summary": clean_summary,
        "live_model": live,
        "disclaimer": "Decision support only; not a replacement for trained responders.",
        "action_pack": action_pack,
        "red_flags": red_flags,
        "red_flag_escalation": bool(red_flags),
        "language": language_code,
        "output_format": format_code,
        "radio_script": build_radio_script(final_label, action_pack, language_code),
        "guidance_basis": build_guidance_basis(final_label, red_flags),
    }
    if red_flags:
        response["scene_summary"] = f"{clean_summary} {red_flag_summary(red_flags)}".strip()
    return response
