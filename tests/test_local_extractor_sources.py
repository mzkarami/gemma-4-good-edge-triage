import os
import tempfile
import unittest
from unittest.mock import patch

import local_extractor


class TestLocalExtractorSources(unittest.TestCase):
    def test_collect_parquet_search_dirs_includes_kaggle_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            kaggle_dir = os.path.join(tmp, "edge-triage-medic")
            os.makedirs(kaggle_dir)
            open(os.path.join(kaggle_dir, "sample.parquet"), "wb").close()

            with patch.dict(os.environ, {"KAGGLE_INPUT_DIR": tmp}, clear=False):
                search_dirs = local_extractor.collect_parquet_search_dirs()

            self.assertIn(kaggle_dir, search_dirs)


if __name__ == "__main__":
    unittest.main()
