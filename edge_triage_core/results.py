"""Shared response-building helpers for Edge-Triage."""

from __future__ import annotations

from .labels import LABEL_METADATA, sanitize_model_text


def build_triage_response(label: str, latency_ms: float, live: bool, scene_summary: str) -> dict:
    meta = LABEL_METADATA[label]
    return {
        "label": label,
        "priority": meta["priority"],
        "next_action": meta["next_action"],
        "latency_ms": round(latency_ms, 2),
        "mode": meta["mode"],
        "scene_summary": sanitize_model_text(scene_summary),
        "live_model": live,
        "disclaimer": "Decision support only; not a replacement for trained responders.",
    }
