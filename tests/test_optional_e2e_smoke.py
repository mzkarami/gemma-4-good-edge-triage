import unittest
from pathlib import Path


class OptionalE2ESmokeScriptTest(unittest.TestCase):
    def test_e2e_smoke_script_documents_opt_in_and_public_contract(self):
        script = Path("scripts/e2e_smoke.sh")
        self.assertTrue(script.exists(), "scripts/e2e_smoke.sh should provide an optional full-stack smoke gate")
        text = script.read_text()

        self.assertIn("EDGE_TRIAGE_RUN_E2E", text)
        self.assertIn("docker compose", text)
        self.assertIn("/healthz", text)
        self.assertIn("/api/triage", text)
        self.assertIn("python3 -m http.server", text)
        self.assertIn("EDGE_TRIAGE_LIVE_MODEL=0", text)
        self.assertIn("pick_free_port", text)
        self.assertNotIn("EDGE_TRIAGE_JUDGE_TOKEN=", text)
        self.assertIn("trap cleanup EXIT", text)

    def test_readme_points_judges_to_optional_e2e_not_default_tests(self):
        readme = Path("README.md").read_text()
        self.assertIn("Optional full-stack smoke", readme)
        self.assertIn("EDGE_TRIAGE_RUN_E2E=1 scripts/e2e_smoke.sh", readme)
        self.assertIn("credential-free fallback mode", readme)


if __name__ == "__main__":
    unittest.main()
