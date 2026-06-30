import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class EvaluationWindowStabilityTest(unittest.TestCase):
    def test_repository_evaluation_window_stability_passes(self):
        subprocess.run([sys.executable, "scripts/check_evaluation_window_stability.py"], check=True)

    def test_missing_stability_surface_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("stub\n")
            script = Path("scripts/check_evaluation_window_stability.py")
            result = subprocess.run([sys.executable, str(script), str(root)], text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing stability surface", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
