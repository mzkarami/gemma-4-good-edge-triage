#!/usr/bin/env python3
"""Fail CI when stale competition-era metric claims leak into public copy."""

from __future__ import annotations

import re
import sys
from pathlib import Path

STALE_METRICS = ["65%", "71.5%", "90.52%"]
PUBLIC_EXTENSIONS = {".md", ".html", ".json"}
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "docs/superpowers/research_logs",
    "docs/reference",
    "docs/plans",
    "docs/CURRENT_FRONTIER.md",
    "results.tsv",
}
REQUIRES_FRONTIER_CONTEXT = re.compile(r"(F1|accuracy|latency|VRAM|samples?)", re.I)


def is_excluded(path: Path, root: Path) -> bool:
    rel = path.relative_to(root).as_posix()
    return any(rel == part or rel.startswith(f"{part}/") for part in EXCLUDED_PARTS)


def iter_public_files(root: Path):
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in PUBLIC_EXTENSIONS and not is_excluded(path, root):
            yield path


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path.cwd()
    failures: list[str] = []
    for path in iter_public_files(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(root).as_posix()
        for metric in STALE_METRICS:
            if metric in text:
                failures.append(f"{rel}: stale public metric claim found: {metric}")
        if REQUIRES_FRONTIER_CONTEXT.search(text) and "docs/CURRENT_FRONTIER.md" not in text and "CURRENT_FRONTIER.md" not in text:
            # Product docs can discuss acceptance criteria without being public metric copy.
            if rel.startswith("docs/product/user-stories/") or rel.startswith("docs/architecture/adr/"):
                continue
            # JSON demo data is source payload consumed by tested pages; pages carry the claim context.
            if rel.endswith("data.json"):
                continue
            # Tests intentionally contain snippets and checker fixtures.
            if rel.startswith("tests/"):
                continue
            failures.append(f"{rel}: metric-related public copy should cite docs/CURRENT_FRONTIER.md")
    if failures:
        print("Public claims check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Public claims check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
