import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
# Ensure we can import prepare.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import prepare

class TestBootloader(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.original_model_dir = prepare.MODEL_DIR
        prepare.MODEL_DIR = self.test_dir.name

    def tearDown(self):
        prepare.MODEL_DIR = self.original_model_dir
        self.test_dir.cleanup()

    @patch("os.path.exists")
    @patch("os.walk")
    def test_download_model_detects_kaggle_input(self, mock_walk, mock_exists):
        # Setup: Kaggle exists and contains the file
        mock_exists.side_effect = lambda p: p == "/kaggle/input" or p == self.test_dir.name
        mock_walk.return_value = [("/kaggle/input/my-dataset", [], ["Edge-Triage-model.gguf"])]

        path = prepare.download_model(filename="model.gguf")

        self.assertEqual(path, "/kaggle/input/my-dataset/Edge-Triage-model.gguf")
        mock_walk.assert_called_once_with("/kaggle/input")

    @patch("prepare.hf_hub_download")
    @patch("os.path.exists")
    @patch("os.rename")
    def test_download_model_falls_back_to_hf_and_prefixes(self, mock_rename, mock_exists, mock_hf):
        # Setup: Kaggle doesn't exist, local doesn't exist
        mock_exists.return_value = False
        mock_hf.return_value = "/tmp/downloaded_file"

        prepare.download_model(repo_id="test/repo", filename="model.gguf")

        # Verify it tried to download the original filename
        mock_hf.assert_called_once_with(repo_id="test/repo", filename="model.gguf", local_dir=prepare.MODEL_DIR)
        
        # Verify it renamed it to include the Edge-Triage- prefix
        expected_target = os.path.join(prepare.MODEL_DIR, "Edge-Triage-model.gguf")
        mock_rename.assert_called_once_with("/tmp/downloaded_file", expected_target)

    @patch.dict(os.environ, {"EDGE_TRIAGE_KAGGLE_MODEL_DATASET": "user/edge-triage-models"}, clear=False)
    @patch("prepare.hf_hub_download")
    @patch("prepare.download_kaggle_dataset")
    @patch("os.path.exists")
    @patch("os.rename")
    def test_download_model_uses_kaggle_dataset_before_hf(self, mock_rename, mock_exists, mock_kaggle, mock_hf):
        def fake_exists(path):
            return path in {
                self.test_dir.name,
                os.path.join(self.test_dir.name, "model.gguf"),
            }

        mock_exists.side_effect = fake_exists

        path = prepare.download_model(repo_id="test/repo", filename="model.gguf")

        expected_target = os.path.join(prepare.MODEL_DIR, "Edge-Triage-model.gguf")
        self.assertEqual(path, expected_target)
        mock_kaggle.assert_called_once_with("user/edge-triage-models", prepare.MODEL_DIR)
        mock_rename.assert_called_once_with(os.path.join(self.test_dir.name, "model.gguf"), expected_target)
        mock_hf.assert_not_called()

    @patch.dict(os.environ, {"EDGE_TRIAGE_KAGGLE_DATASET": "user/edge-triage-shards"}, clear=False)
    @patch("prepare.download_kaggle_dataset")
    @patch("prepare.Pool")
    @patch("os.path.exists")
    def test_download_data_uses_kaggle_dataset_before_hf_workers(self, mock_exists, mock_pool, mock_kaggle):
        kaggle_downloaded = {"ready": False}

        def fake_kaggle(*_args):
            kaggle_downloaded["ready"] = True
            return True

        def fake_exists(path):
            if path == prepare.DATA_DIR:
                return True
            return kaggle_downloaded["ready"] and (
                path.endswith("shard_00000.parquet") or path.endswith("shard_06542.parquet")
            )

        mock_kaggle.side_effect = fake_kaggle
        mock_exists.side_effect = fake_exists

        prepare.download_data(num_shards=1, download_workers=8)

        mock_kaggle.assert_called_once_with("user/edge-triage-shards", prepare.DATA_DIR)
        mock_pool.assert_not_called()

    @patch("prepare.download_model")
    def test_download_multimodal_projector_fetches_f16_projector_with_edge_triage_name(self, mock_download_model):
        expected_path = os.path.join(prepare.MODEL_DIR, "Edge-Triage-mmproj-F16.gguf")
        mock_download_model.return_value = expected_path

        path = prepare.download_multimodal_projector()

        self.assertEqual(path, expected_path)
        mock_download_model.assert_called_once_with(
            repo_id="unsloth/gemma-4-e4b-it-GGUF",
            filename="mmproj-F16.gguf",
        )

if __name__ == "__main__":
    unittest.main()
