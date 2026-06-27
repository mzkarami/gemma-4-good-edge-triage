#!/usr/bin/env python3
"""Check local Markdown links.

This intentionally ignores external URLs, mailto links, and generated/virtual
environment directories. It validates relative file links and same-file anchors
well enough to catch stale documentation moves in CI.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {
    ".git",
    ".github",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
AUTO_RE = re.compile(r"<((?:https?://|mailto:)[^>]+)>")
EXTERNAL_PREFIXES = (
    "http://",
    "https://",
    "mailto:",
    "tel:",
)


def iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*.md"):
        if SKIP_PARTS.intersection(path.relative_to(ROOT).parts):
            continue
        files.append(path)
    return sorted(files)


def clean_target(raw: str) -> str:
    target = raw.strip()
    if not target or target.startswith("#"):
        return ""
    if " " in target and not target.startswith("<"):
        # Strip optional title: [text](path "title")
        target = target.split(" ", 1)[0]
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    return unquote(target)


def is_external(target: str) -> bool:
    return target.startswith(EXTERNAL_PREFIXES)


def existing_anchor_file(source: Path, target: str) -> Path:
    path_part = target.split("#", 1)[0]
    if not path_part:
        return source
    return (source.parent / path_part).resolve()


def main() -> int:
    errors: list[str] = []
    for md in iter_markdown_files():
        text = md.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            raw = match.group(1)
            if raw in {m.group(1) for m in AUTO_RE.finditer(text)}:
                continue
            target = clean_target(raw)
            if not target or is_external(target):
                continue
            path = existing_anchor_file(md, target)
            try:
                path.relative_to(ROOT)
            except ValueError:
                errors.append(f"{md.relative_to(ROOT)}: link escapes repo: {raw}")
                continue
            if not path.exists():
                errors.append(f"{md.relative_to(ROOT)}: missing link target: {raw}")
    if errors:
        print("Markdown link check failed:")
        for err in errors:
            print(f"- {err}")
        return 1
    print(f"Markdown link check passed ({len(iter_markdown_files())} files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
