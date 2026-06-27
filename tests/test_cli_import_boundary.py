import builtins
import importlib.util
import os
import subprocess
import sys
import unittest
from unittest.mock import patch


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI_PATH = os.path.join(REPO_ROOT, "edge-triage-cli.py")


class CliImportBoundaryTest(unittest.TestCase):
    def test_importing_cli_does_not_import_research_sandbox(self):
        real_import = builtins.__import__

        def guarded_import(name, *args, **kwargs):
            if name == "triage_sandbox" or name.startswith("triage_sandbox."):
                raise AssertionError("field CLI must not import triage_sandbox")
            return real_import(name, *args, **kwargs)

        with patch.object(builtins, "__import__", side_effect=guarded_import):
            spec = importlib.util.spec_from_file_location("edge_triage_cli_boundary", CLI_PATH)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

    def test_cli_help_does_not_trigger_sandbox_startup(self):
        env = dict(os.environ)
        env["PYTHONPATH"] = REPO_ROOT + os.pathsep + env.get("PYTHONPATH", "")
        result = subprocess.run(
            [sys.executable, CLI_PATH, "--help"],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Edge-Triage Field Tool", result.stdout)
        self.assertNotIn("Sandbox:", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
