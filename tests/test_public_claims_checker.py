import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class PublicClaimsCheckerTest(unittest.TestCase):
    def test_repository_public_claims_pass(self):
        subprocess.run([sys.executable, "scripts/check_public_claims.py"], check=True)

    def test_stale_metric_claim_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("Old claim: 90.52% accuracy.\n")
            script = Path("scripts/check_public_claims.py")
            result = subprocess.run([sys.executable, str(script), str(root)], text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("stale public metric", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
