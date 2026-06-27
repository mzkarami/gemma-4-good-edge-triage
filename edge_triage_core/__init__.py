"""Shared product contracts for Edge-Triage.

This package is intentionally pure and lightweight. It must stay safe to import
from field tools, the public live API, and tests without triggering model
loads, artifact downloads, CUDA probes, or benchmark setup.
"""

from .config import TriageRuntimeConfig
from .labels import CANONICAL_CATEGORIES, LABEL_METADATA
from .prompts import TRIAGE_SYSTEM_PROMPT, resolve_main_prompt_template
from .results import build_triage_response

__all__ = [
    "CANONICAL_CATEGORIES",
    "LABEL_METADATA",
    "TRIAGE_SYSTEM_PROMPT",
    "TriageRuntimeConfig",
    "build_triage_response",
    "resolve_main_prompt_template",
]
