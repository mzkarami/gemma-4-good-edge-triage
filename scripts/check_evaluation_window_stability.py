#!/usr/bin/env python3
"""Check evaluation-window stability surfaces for closed-but-active submissions."""

from __future__ import annotations

import sys
from pathlib import Path

REQUIRED_PATHS = [
    "README.md",
    "docs/README.md",
    "docs/CURRENT_FRONTIER.md",
    "docs/KAGGLE_SUBMISSION.md",
    "docs/KAGGLE_SUBMISSION_FINAL.md",
    "docs/KAGGLE_WRITEUP.md",
    "docs/VIDEO_SCRIPT.md",
    "docs/submission/README.md",
    "docs/product/evaluation-window-stability.md",
    "site/index.html",
    "site/app.html",
    "site/judge.html",
    "site/metrics.html",
]

REQUIRED_STABILITY_PHRASES = [
    "submission package is closed",
    "judges may still evaluate",
    "maintained public project artifact",
    "docs/CURRENT_FRONTIER.md",
    "https://kaggle.nelly.work/index.html#volunteer",
]

SUBMISSION_REFERENCE_PHRASES = [
    "submitted-package reference material",
    "not obsolete or abandoned",
    "docs/CURRENT_FRONTIER.md",
]

FORBIDDEN_STABILITY_PHRASES = [
    "submitted docs are obsolete",
    "submission docs are obsolete",
    "resubmit to kaggle",
]


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path.cwd()
    failures: list[str] = []

    for rel in REQUIRED_PATHS:
        if not (root / rel).exists():
            failures.append(f"missing stability surface: {rel}")

    stability_path = root / "docs/product/evaluation-window-stability.md"
    if stability_path.exists():
        text = stability_path.read_text(encoding="utf-8").lower()
        for phrase in REQUIRED_STABILITY_PHRASES:
            if phrase.lower() not in text:
                failures.append(f"docs/product/evaluation-window-stability.md missing phrase: {phrase}")
        for phrase in FORBIDDEN_STABILITY_PHRASES:
            if phrase in text:
                failures.append(f"docs/product/evaluation-window-stability.md contains risky phrase: {phrase}")

    submission_path = root / "docs/submission/README.md"
    if submission_path.exists():
        submission_text = submission_path.read_text(encoding="utf-8").lower()
        for phrase in SUBMISSION_REFERENCE_PHRASES:
            if phrase.lower() not in submission_text:
                failures.append(f"docs/submission/README.md missing phrase: {phrase}")

    if failures:
        print("Evaluation-window stability check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Evaluation-window stability check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
