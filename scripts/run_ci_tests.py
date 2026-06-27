#!/usr/bin/env python3
"""Run the Edge-Triage CI-safe validation suite.

This suite intentionally avoids tests that import native model runtimes at module
import time. GitHub-hosted runners can SIGILL on llama.cpp/torch wheels even when
project logic is fine; native/full checks belong in run_full_local_tests.py on a
maintainer machine.
"""

from __future__ import annotations

import subprocess
import sys

CI_SAFE_MODULES = [
    "tests.test_bootloader",
    "tests.test_cli_import_boundary",
    "tests.test_edge_triage_core",
    "tests.test_field_tool",
    "tests.test_live_api",
    "tests.test_live_api_security_controls",
    "tests.test_live_deployment",
    "tests.test_local_extractor_sources",
    "tests.test_optional_e2e_smoke",
    "tests.test_site_live_ui",
]


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def main() -> int:
    run([sys.executable, "scripts/check_docs_links.py"])
    run([sys.executable, "-m", "unittest", *CI_SAFE_MODULES, "-v"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
