#!/usr/bin/env python3
"""Run full local Edge-Triage validation on a maintainer machine.

This enables native sandbox tests explicitly. Use this before changing benchmark,
model-runtime, prompt-routing, or frontier behavior. CI uses run_ci_tests.py.
"""

from __future__ import annotations

import os
import subprocess
import sys


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True, env=env)


def main() -> int:
    env = dict(os.environ)
    env.setdefault("EDGE_TRIAGE_RUN_NATIVE_TESTS", "1")

    run([sys.executable, "scripts/check_docs_links.py"], env=env)
    run(["git", "diff", "--check"], env=env)
    run([sys.executable, "-m", "unittest", "discover", "tests/", "-v"], env=env)
    run([sys.executable, "edge-triage-cli.py", "--help"], env=env)
    run([sys.executable, "triage_sandbox.py", "--help"], env=env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
