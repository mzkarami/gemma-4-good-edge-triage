import importlib
import io
import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image


class LiveApiTest(unittest.TestCase):
    def setUp(self):
        os.environ["EDGE_TRIAGE_JUDGE_TOKEN"] = "test-token"
        os.environ["EDGE_TRIAGE_LIVE_MODEL"] = "0"
        os.environ["EDGE_TRIAGE_RATE_LIMIT_PER_MINUTE"] = "100"
        os.environ["EDGE_TRIAGE_RATE_LIMIT_PER_DAY"] = "1000"
        import live_api
        self.live_api = importlib.reload(live_api)
        self.client = TestClient(self.live_api.app)

    def make_png(self):
        buf = io.BytesIO()
        Image.new("RGB", (8, 8), color=(255, 0, 0)).save(buf, format="PNG")
        return buf.getvalue()

    def post_image(self, token="test-token", data=None, content_type="image/png", filename="bridge.png", note="bridge washed out after flood"):
        headers = {"Authorization": f"Bearer {token}"} if token is not None else {}
        payload = data if data is not None else self.make_png()
        return self.client.post(
            "/api/triage",
            headers=headers,
            data={"note": note},
            files={"image": (filename, payload, content_type)},
        )

    def test_healthz_is_public(self):
        for path in ("/healthz", "/api/healthz"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"ok": True})

    def test_triage_requires_token(self):
        response = self.post_image(token=None)
        self.assertEqual(response.status_code, 401)

    def test_triage_rejects_wrong_token(self):
        response = self.post_image(token="wrong")
        self.assertEqual(response.status_code, 403)

    def test_triage_rejects_upload_above_25mb(self):
        oversized = b"x" * (25 * 1024 * 1024 + 1)
        response = self.post_image(data=oversized, content_type="image/png")
        self.assertEqual(response.status_code, 413)

    def test_triage_rejects_unsupported_mime_type(self):
        response = self.post_image(data=b"hello", content_type="text/plain", filename="note.txt")
        self.assertEqual(response.status_code, 415)

    def test_triage_rejects_corrupt_png_without_stack_trace(self):
        corrupt_png = b"\x89PNG\r\n\x1a\n" + b"not a valid png body"
        response = self.post_image(data=corrupt_png, content_type="image/png", filename="corrupt.png")
        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.json(), {"detail": "Uploaded file is not a valid image."})

    def test_triage_returns_safe_json_for_valid_image(self):
        response = self.post_image()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        for key in ["label", "priority", "next_action", "latency_ms", "mode", "scene_summary", "disclaimer"]:
            self.assertIn(key, body)
        self.assertEqual(body["label"], "infrastructure_and_utility_damage")
        self.assertIn("fallback", body["scene_summary"].lower())
        self.assertIn("decision support", body["disclaimer"].lower())
        self.assertNotIn("raw_output", body)

    def test_fallback_routes_firefighter_scene_to_disaster_response(self):
        response = self.post_image(filename="firefighter-forest-fire.jpg", note="fireman extinguishing a forest fire")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["label"], "rescue_volunteering_or_donation_effort")
        self.assertNotEqual(body["priority"], "No disaster triage action")
        self.assertIn("live visual gemma was not active", body["scene_summary"].lower())

    def test_live_output_parses_bounded_scene_summary(self):
        label, summary = self.live_api.parse_live_output(
            '{"label":"infrastructure_and_utility_damage","scene_summary":"A firefighter is extinguishing a forest fire near trees."}'
        )
        self.assertEqual(label, "infrastructure_and_utility_damage")
        self.assertEqual(summary, "A firefighter is extinguishing a forest fire near trees.")

    def test_live_output_redacts_secret_like_text_from_scene_summary(self):
        label, summary = self.live_api.parse_live_output(
            '{"label":"not_humanitarian","scene_summary":"token: abc123 visible on a sign"}'
        )
        self.assertEqual(label, "not_humanitarian")
        self.assertNotIn("abc123", summary)

    def test_temp_upload_is_deleted_after_request(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(self.live_api, "TEMP_ROOT", tmpdir):
                response = self.post_image()
                self.assertEqual(response.status_code, 200)
                self.assertEqual(os.listdir(tmpdir), [])

    def test_model_requests_are_serialized(self):
        self.assertTrue(hasattr(self.live_api, "MODEL_LOCK"))
        self.assertFalse(self.live_api.MODEL_LOCK.locked())


if __name__ == "__main__":
    unittest.main()
