import unittest
from pathlib import Path


class LiveDeploymentConfigTest(unittest.TestCase):
    def test_live_api_dockerfile_exists_and_runs_uvicorn(self):
        dockerfile = Path("Dockerfile.live-api")
        self.assertTrue(dockerfile.exists())
        text = dockerfile.read_text()
        self.assertIn("uvicorn", text)
        self.assertIn("live_api:app", text)
        self.assertNotIn("uv sync", text)
        self.assertIn("fastapi", text)
        self.assertIn("llama-cpp-python", text)
        self.assertIn("Edge-Triage-gemma-4-E4B-it-Q3_K_M.gguf", text)
        self.assertIn("build-essential", text)
        self.assertIn("cmake", text)

    def test_compose_live_api_is_profiled_and_private_by_default(self):
        compose = Path("docker-compose.yml").read_text()
        self.assertIn("edge-triage-live-api:", compose)
        self.assertIn("profiles:", compose)
        self.assertIn("live", compose)
        self.assertIn("${LIVE_API_BIND_ADDRESS:-127.0.0.1}:4180:8080", compose)
        self.assertIn("EDGE_TRIAGE_MAX_UPLOAD_MB=25", compose)
        self.assertIn("EDGE_TRIAGE_PUBLIC_API_ENABLED=${EDGE_TRIAGE_PUBLIC_API_ENABLED:-1}", compose)
        self.assertIn("EDGE_TRIAGE_MAX_CONCURRENT_REQUESTS=${EDGE_TRIAGE_MAX_CONCURRENT_REQUESTS:-2}", compose)
        self.assertIn("EDGE_TRIAGE_MODEL_PATH=${EDGE_TRIAGE_MODEL_PATH:-/app/models/Edge-Triage-gemma-4-E4B-it-Q3_K_M.gguf}", compose)
        self.assertIn("EDGE_TRIAGE_MMPROJ_PATH=${EDGE_TRIAGE_MMPROJ_PATH:-/app/models/Edge-Triage-mmproj-F16.gguf}", compose)
        self.assertIn("/tmp/edge-triage-live:mode=1777,noexec,nosuid,nodev,size=64m", compose)
        self.assertIn("TMPDIR=/tmp/edge-triage-live", compose)
        self.assertIn("${EDGE_TRIAGE_MODEL_DIR:-/home/dev/.cache/autoresearch/models}:/app/models:ro", compose)
        self.assertIn("no-new-privileges:true", compose)
        self.assertIn("cap_drop:", compose)
        self.assertIn("read_only: true", compose)
        self.assertNotIn('tempfile.gettempdir())', Path("live_api.py").read_text())

    def test_nginx_can_proxy_live_api_without_serving_raw_repo(self):
        nginx = Path("deploy/nginx.conf").read_text()
        self.assertIn("client_max_body_size 25m", nginx)
        self.assertIn("location /api/", nginx)
        self.assertIn("edge-triage-live-api:8080", nginx)
        self.assertIn("proxy_pass $live_api$request_uri", nginx)

    def test_nginx_blocks_repo_internal_paths_before_spa_fallback(self):
        nginx = Path("deploy/nginx.conf").read_text()
        self.assertIn("location ~ (^|/)\\.", nginx)
        self.assertIn("^/(docs|models|logs|data|notebooks?)(/|$)", nginx)
        self.assertIn("results\\.tsv", nginx)
        self.assertIn("submission_notebook\\.ipynb", nginx)


if __name__ == "__main__":
    unittest.main()
