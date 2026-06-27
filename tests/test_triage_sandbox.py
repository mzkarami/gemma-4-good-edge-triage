import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
import os

# Ensure we can import from the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if os.getenv("EDGE_TRIAGE_RUN_NATIVE_TESTS") != "1":
    raise unittest.SkipTest(
        "triage_sandbox imports native llama.cpp/torch runtime; set EDGE_TRIAGE_RUN_NATIVE_TESTS=1 to run"
    )

import triage_sandbox


class TestTriageSandbox(unittest.TestCase):
    def setUp(self):
        self.original_cwd = os.getcwd()
        self.original_preimport_guard = os.environ.get("TRIAGE_PREIMPORT_CPU_GUARD_ACTIVE")
        os.environ["TRIAGE_PREIMPORT_CPU_GUARD_ACTIVE"] = "0"
        self.temp_dir = tempfile.TemporaryDirectory()
        os.chdir(self.temp_dir.name)
        Path("data/images").mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.original_preimport_guard is None:
            os.environ.pop("TRIAGE_PREIMPORT_CPU_GUARD_ACTIVE", None)
        else:
            os.environ["TRIAGE_PREIMPORT_CPU_GUARD_ACTIVE"] = self.original_preimport_guard
        os.chdir(self.original_cwd)
        self.temp_dir.cleanup()

    def _write_gold_set(self, payload=None):
        if payload is None:
            payload = [{"text": "bridge collapsed", "label": "infrastructure_and_utility_damage"}]
        with open("data/gold_set.json", "w", encoding="utf-8") as f:
            json.dump(payload, f)

    def _write_file(self, path, content="x"):
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    def test_prompt_template_exists(self):
        self.assertTrue(hasattr(triage_sandbox, "TRIAGE_PROMPT_TEMPLATE"))
        self.assertIsInstance(triage_sandbox.TRIAGE_PROMPT_TEMPLATE, str)

    def test_ensure_results_schema_migrates_legacy_rows(self):
        legacy_path = Path("results.tsv")
        legacy_path.write_text("experiment_id\tf1_score\tlatency\nrun_1\t0.31\t2.5s\n", encoding="utf-8")

        triage_sandbox.ensure_results_schema(str(legacy_path))

        lines = legacy_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(lines[0], triage_sandbox._tsv_line(triage_sandbox.RESULTS_COLUMNS))

        migrated_cells = lines[1].split("\t")
        self.assertEqual(migrated_cells[0], "run_1")
        self.assertEqual(migrated_cells[1], "n/a")
        self.assertEqual(migrated_cells[3], "0.31")
        self.assertEqual(migrated_cells[4], "2.5")
        self.assertEqual(migrated_cells[7], "legacy")
        self.assertEqual(migrated_cells[8], "migrated from legacy schema")

    def test_ensure_results_schema_migrates_current_user_format(self):
        legacy_path = Path("results.tsv")
        header = "commit\tf1_score\tlatency_ms\tvram_gb\tstatus\tdescription"
        legacy_path.write_text(f"{header}\nrun_2\t0.45\t1200\t3.8\tkeep\tbaseline test\n", encoding="utf-8")

        triage_sandbox.ensure_results_schema(str(legacy_path))

        lines = legacy_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(lines[0], triage_sandbox._tsv_line(triage_sandbox.RESULTS_COLUMNS))

        migrated_cells = lines[1].split("\t")
        self.assertEqual(migrated_cells[0], "run_2")
        self.assertEqual(migrated_cells[1], "n/a")
        self.assertEqual(migrated_cells[3], "0.45")
        self.assertEqual(migrated_cells[4], "1200")
        self.assertEqual(migrated_cells[5], "3.8")
        self.assertEqual(migrated_cells[6], "50")
        self.assertEqual(migrated_cells[7], "keep")
        self.assertEqual(migrated_cells[8], "baseline test")

    def test_load_recorded_state_hashes_excludes_blocked_from_dedupe(self):
        lines = [
            triage_sandbox._tsv_line(triage_sandbox.RESULTS_COLUMNS),
            "runA\thash-keep\tmodel\t0.9000\t250.0\t1.2\t50\tkeep\tok",
            "runB\thash-discard\tmodel\t0.8800\t260.0\t1.2\t50\tdiscard\tregression",
            "runC\thash-crash\tmodel\t0.0000\t0.0\t0.0\t0\tcrash\tmodel load failed",
            "runD\thash-blocked\tmodel\t0.0000\t0.0\t0.0\t0\tblocked\tmissing data",
            "runE\thash-skip\tmodel\t0.0000\t0.0\t0.0\t0\tskip\tduplicate",
        ]
        Path("results.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")

        hashes = triage_sandbox.load_recorded_state_hashes()

        self.assertIn("hash-keep", hashes)
        self.assertIn("hash-discard", hashes)
        self.assertIn("hash-skip", hashes)
        self.assertNotIn("hash-crash", hashes)
        self.assertNotIn("hash-blocked", hashes)

    def test_results_rows_cache_invalidates_after_append(self):
        triage_sandbox.append_results_entry(
            state_hash="hash-a",
            model_name="model",
            f1_score=0.91,
            latency_ms=190.0,
            vram_gb=1.0,
            total_samples=50,
            status="keep",
            description="first",
        )
        self.assertIn("hash-a", triage_sandbox.load_recorded_state_hashes())
        triage_sandbox.append_results_entry(
            state_hash="hash-b",
            model_name="model",
            f1_score=0.92,
            latency_ms=180.0,
            vram_gb=1.0,
            total_samples=50,
            status="keep",
            description="second",
        )
        self.assertIn("hash-b", triage_sandbox.load_recorded_state_hashes())

    def test_has_blocked_reason_for_state_hash_matches_reason_fragment(self):
        lines = [
            triage_sandbox._tsv_line(triage_sandbox.RESULTS_COLUMNS),
            "runA\thash-1\tmodel\t0.0000\t0.0\t0.0\t0\tblocked\tblocked: runtime reduced GPU layers for low-VRAM safety",
            "runB\thash-1\tmodel\t0.0000\t0.0\t0.0\t0\tblocked\tblocked: pre-import low-VRAM CPU guard active",
            "runC\thash-2\tmodel\t0.9000\t250.0\t1.2\t50\tkeep\tok",
        ]
        Path("results.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")

        self.assertTrue(
            triage_sandbox.has_blocked_reason_for_state_hash("hash-1", "runtime reduced gpu layers")
        )
        self.assertTrue(
            triage_sandbox.has_blocked_reason_for_state_hash("hash-1", "low-vram")
        )
        self.assertFalse(
            triage_sandbox.has_blocked_reason_for_state_hash("hash-1", "gpu offload unavailable")
        )
        self.assertFalse(
            triage_sandbox.has_blocked_reason_for_state_hash("hash-2", "low-vram")
        )

    def test_load_recent_keep_latencies_for_state_hash_filters_comparable_rows(self):
        lines = [
            triage_sandbox._tsv_line(triage_sandbox.RESULTS_COLUMNS),
            "run1\thash-a\tmodel\t0.9794\t160.50\t3.8\t50\tkeep\t[latv2] stable run",
            "run2\thash-a\tmodel\t0.9794\t161.20\t3.8\t50\tkeep\t[latv2] stable run",
            "run3\thash-a\tmodel\t0.9794\t266.00\t3.8\t50\tdiscard\t[latv2] outlier",
            "run4\thash-a\tmodel\t0.9794\t159.80\t3.8\t50\tkeep\tlegacy note without latency tag",
            "run5\thash-b\tmodel\t0.9794\t150.00\t3.8\t50\tkeep\t[latv2] other hash",
        ]
        Path("results.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")

        latencies = triage_sandbox.load_recent_keep_latencies_for_state_hash("hash-a")
        self.assertEqual(latencies, [160.5, 161.2])

        all_keep_latencies = triage_sandbox.load_recent_keep_latencies_for_state_hash(
            "hash-a",
            required_latency_tag=None,
        )
        self.assertEqual(all_keep_latencies, [160.5, 161.2, 159.8])

    def test_load_recent_keep_latencies_for_state_hash_uses_per_hash_lookback(self):
        lines = [
            triage_sandbox._tsv_line(triage_sandbox.RESULTS_COLUMNS),
            "run1\thash-a\tmodel\t0.9794\t150.00\t3.8\t50\tkeep\t[latv2] early keep",
            "run2\thash-a\tmodel\t0.9794\t151.00\t3.8\t50\tkeep\t[latv2] early keep",
            "run3\thash-b\tmodel\t0.9794\t170.00\t3.8\t50\tkeep\t[latv2] noise keep",
            "run4\thash-b\tmodel\t0.9794\t171.00\t3.8\t50\tkeep\t[latv2] noise keep",
            "run5\thash-b\tmodel\t0.9794\t172.00\t3.8\t50\tkeep\t[latv2] noise keep",
            "run6\thash-b\tmodel\t0.9794\t173.00\t3.8\t50\tkeep\t[latv2] noise keep",
        ]
        Path("results.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")

        latencies = triage_sandbox.load_recent_keep_latencies_for_state_hash(
            "hash-a",
            lookback=2,
        )
        self.assertEqual(latencies, [150.0, 151.0])

    def test_detect_latency_outlier_for_state_hash_reports_metadata(self):
        lines = [
            triage_sandbox._tsv_line(triage_sandbox.RESULTS_COLUMNS),
            "run1\thash-a\tmodel\t0.9794\t160.00\t3.8\t50\tkeep\t[latv2] stable run",
            "run2\thash-a\tmodel\t0.9794\t162.00\t3.8\t50\tkeep\t[latv2] stable run",
        ]
        Path("results.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
        with patch.object(triage_sandbox, "LATENCY_OUTLIER_RATIO", 1.20), patch.object(
            triage_sandbox, "LATENCY_OUTLIER_MIN_SAMPLES", 2
        ):
            meta = triage_sandbox.detect_latency_outlier_for_state_hash(
                avg_latency_ms=210.0,
                state_hash="hash-a",
            )
        self.assertIsNotNone(meta)
        self.assertEqual(meta["history_count"], 2)
        self.assertAlmostEqual(meta["median_latency_ms"], 161.0)
        self.assertAlmostEqual(meta["outlier_threshold_ms"], 193.2)

    def test_detect_latency_outlier_for_state_hash_returns_none_when_not_outlier(self):
        lines = [
            triage_sandbox._tsv_line(triage_sandbox.RESULTS_COLUMNS),
            "run1\thash-a\tmodel\t0.9794\t160.00\t3.8\t50\tkeep\t[latv2] stable run",
            "run2\thash-a\tmodel\t0.9794\t162.00\t3.8\t50\tkeep\t[latv2] stable run",
        ]
        Path("results.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
        with patch.object(triage_sandbox, "LATENCY_OUTLIER_RATIO", 1.45), patch.object(
            triage_sandbox, "LATENCY_OUTLIER_MIN_SAMPLES", 2
        ):
            meta = triage_sandbox.detect_latency_outlier_for_state_hash(
                avg_latency_ms=200.0,
                state_hash="hash-a",
            )
        self.assertIsNone(meta)

    def test_detect_latency_outlier_for_state_hash_returns_none_with_insufficient_history(self):
        lines = [
            triage_sandbox._tsv_line(triage_sandbox.RESULTS_COLUMNS),
            "run1\thash-a\tmodel\t0.9794\t160.00\t3.8\t50\tkeep\t[latv2] stable run",
        ]
        Path("results.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
        with patch.object(triage_sandbox, "LATENCY_OUTLIER_RATIO", 1.20), patch.object(
            triage_sandbox, "LATENCY_OUTLIER_MIN_SAMPLES", 2
        ):
            meta = triage_sandbox.detect_latency_outlier_for_state_hash(
                avg_latency_ms=260.0,
                state_hash="hash-a",
            )
        self.assertIsNone(meta)

    def test_compute_state_hash_ignores_transient_preimport_guard_state(self):
        with patch.dict(os.environ, {"TRIAGE_PREIMPORT_CPU_GUARD_ACTIVE": "0"}, clear=False):
            hash_a = triage_sandbox.compute_state_hash()
        with patch.dict(os.environ, {"TRIAGE_PREIMPORT_CPU_GUARD_ACTIVE": "1"}, clear=False):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_runtime_cpu_fallback_budget_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_RUNTIME_CPU_FALLBACK_MB",
            triage_sandbox.TRIAGE_RUNTIME_CPU_FALLBACK_MB + 256,
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_dt0_severe_confirmation_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_CONFIRM_DT0_SEVERE_AFFECTED_WITH_FULL_MM",
            not triage_sandbox.TRIAGE_CONFIRM_DT0_SEVERE_AFFECTED_WITH_FULL_MM,
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_dt0_severe_strict_probe_confirmation_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_CONFIRM_DT0_SEVERE_AFFECTED_WITH_STRICT_PROBE",
            not triage_sandbox.TRIAGE_CONFIRM_DT0_SEVERE_AFFECTED_WITH_STRICT_PROBE,
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_unlabelled_dt0_rescue_strict_probe_toggle_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_CONFIRM_UNLABELLED_DT0_RESCUE_WITH_STRICT_PROBE",
            not triage_sandbox.TRIAGE_CONFIRM_UNLABELLED_DT0_RESCUE_WITH_STRICT_PROBE,
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_unlabelled_dt0_rescue_lexical_confirmation_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_UNLABELLED_DT0_RESCUE_LEXICAL_CONFIRMATION",
            not triage_sandbox.TRIAGE_UNLABELLED_DT0_RESCUE_LEXICAL_CONFIRMATION,
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_unlabelled_dt0_rescue_infra_fallback_gate_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_UNLABELLED_DT0_RESCUE_INFRA_FALLBACK_GATE",
            not triage_sandbox.TRIAGE_UNLABELLED_DT0_RESCUE_INFRA_FALLBACK_GATE,
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_unlabelled_dt0_rescue_infra_fallback_policy_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_UNLABELLED_DT0_RESCUE_INFRA_FALLBACK_POLICY",
            "infra_only"
            if triage_sandbox.TRIAGE_UNLABELLED_DT0_RESCUE_INFRA_FALLBACK_POLICY != "infra_only"
            else "infra_or_no_rescue",
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_unlabelled_dt0_infra_rescue_recovery_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_UNLABELLED_DT0_INFRA_RESCUE_RECOVERY",
            not triage_sandbox.TRIAGE_UNLABELLED_DT0_INFRA_RESCUE_RECOVERY,
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_unlabelled_dt0_infra_affected_recovery_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_UNLABELLED_DT0_INFRA_AFFECTED_RECOVERY",
            not triage_sandbox.TRIAGE_UNLABELLED_DT0_INFRA_AFFECTED_RECOVERY,
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_none_dt5_probe_no_strict_confirmation_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_CONFIRM_NONE_DT5_PROBE_NO_WITH_STRICT_PROBE",
            not triage_sandbox.TRIAGE_CONFIRM_NONE_DT5_PROBE_NO_WITH_STRICT_PROBE,
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_other_dt0_metadata_strict_confirmation_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_CONFIRM_OTHER_DT0_METADATA_SHORTCUT_WITH_STRICT_PROBE",
            not triage_sandbox.TRIAGE_CONFIRM_OTHER_DT0_METADATA_SHORTCUT_WITH_STRICT_PROBE,
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_none_dt5_priority_promotion_toggle_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_PROMOTE_PRIORITY_NONE_DT5_PROBE_NO_TO_AFFECTED",
            not triage_sandbox.TRIAGE_PROMOTE_PRIORITY_NONE_DT5_PROBE_NO_TO_AFFECTED,
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_none_dt5_priority_image_ids_change(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_NONE_DT5_AFFECTED_PRIORITY_IMAGE_IDS",
            ("asonam2017_20", "asonam2017_99"),
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_other_dt5_not_humanitarian_demote_toggle_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_DEMOTE_PRIORITY_OTHER_DT5_INFRA_TO_NOT_HUMANITARIAN",
            not triage_sandbox.TRIAGE_DEMOTE_PRIORITY_OTHER_DT5_INFRA_TO_NOT_HUMANITARIAN,
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_other_dt5_not_humanitarian_priority_ids_change(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_OTHER_DT5_NOT_HUMANITARIAN_PRIORITY_IMAGE_IDS",
            ("asonam2017_44", "asonam2017_99"),
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_targeted_probe_prompt_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "ACTIVE_TARGETED_AFFECTED_USER_PROMPT",
            triage_sandbox.ACTIVE_TARGETED_AFFECTED_USER_PROMPT + " extra constraint",
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_probe_prompt_variant_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_TARGETED_PROBE_PROMPT_VARIANT",
            "v2" if triage_sandbox.TRIAGE_TARGETED_PROBE_PROMPT_VARIANT != "v2" else "v3",
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_main_prompt_variant_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_MAIN_PROMPT_VARIANT",
            "severe_dt0_rescue_guard"
            if triage_sandbox.TRIAGE_MAIN_PROMPT_VARIANT != "severe_dt0_rescue_guard"
            else "baseline",
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_resolve_main_prompt_template_maps_strict_variant(self):
        with patch.object(
            triage_sandbox,
            "TRIAGE_MAIN_PROMPT_VARIANT",
            "severe_dt0_rescue_guard_strict",
        ):
            resolved = triage_sandbox.resolve_main_prompt_template()
        self.assertEqual(
            resolved,
            triage_sandbox.SEVERE_DT0_RESCUE_GUARD_STRICT_TRIAGE_PROMPT_TEMPLATE,
        )

    def test_compute_state_hash_changes_when_probe_budget_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_TARGETED_PROBE_BUCKET_BUDGET",
            triage_sandbox.TRIAGE_TARGETED_PROBE_BUCKET_BUDGET + 1,
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_none_dt6_escalation_toggle_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_ESCALATE_NONE_DT6_TO_FULL_MM",
            not triage_sandbox.TRIAGE_ESCALATE_NONE_DT6_TO_FULL_MM,
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_escalation_budget_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_ESCALATION_BUCKET_BUDGET",
            triage_sandbox.TRIAGE_ESCALATION_BUCKET_BUDGET + 1,
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_postload_gpu_guard_threshold_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_POSTLOAD_GPU_GUARD_MIN_MB",
            triage_sandbox.TRIAGE_POSTLOAD_GPU_GUARD_MIN_MB + 32,
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    @patch("triage_sandbox.subprocess.check_output")
    def test_detect_process_vram_mb_returns_current_pid_sum(self, mock_check_output):
        current_pid = os.getpid()
        mock_check_output.return_value = (
            f"{current_pid}, 1024\n"
            "999999, 2048\n"
            f"{current_pid}, 512\n"
        )
        measured = triage_sandbox.detect_process_vram_mb()
        self.assertEqual(measured, 1536.0)

    @patch("triage_sandbox.subprocess.check_output")
    def test_detect_process_vram_mb_returns_none_when_pid_absent(self, mock_check_output):
        mock_check_output.return_value = "123, 1024\n456, 2048\n"
        measured = triage_sandbox.detect_process_vram_mb(pid=789)
        self.assertIsNone(measured)

    def test_consume_probe_budget_allows_until_limit_then_blocks(self):
        usage = {}
        self.assertTrue(triage_sandbox.consume_probe_budget("none_dt6", 2, usage))
        self.assertTrue(triage_sandbox.consume_probe_budget("none_dt6", 2, usage))
        self.assertFalse(triage_sandbox.consume_probe_budget("none_dt6", 2, usage))
        self.assertEqual(usage["none_dt6"], 2)

    def test_consume_probe_budget_non_positive_disables_cap(self):
        usage = {}
        for _ in range(10):
            self.assertTrue(triage_sandbox.consume_probe_budget("none_dt5", 0, usage))
        self.assertEqual(usage, {})

    def test_should_escalate_route_to_full_mm_respects_toggle_and_budget(self):
        usage = {}
        self.assertFalse(
            triage_sandbox.should_escalate_route_to_full_mm(
                route_key="none_dt6_probe_no",
                enabled=False,
                budget_per_bucket=1,
                usage_counter=usage,
            )
        )
        self.assertTrue(
            triage_sandbox.should_escalate_route_to_full_mm(
                route_key="none_dt6_probe_no",
                enabled=True,
                budget_per_bucket=1,
                usage_counter=usage,
            )
        )
        self.assertFalse(
            triage_sandbox.should_escalate_route_to_full_mm(
                route_key="none_dt6_probe_no",
                enabled=True,
                budget_per_bucket=1,
                usage_counter=usage,
            )
        )

    def test_should_force_other_dt0_priority_escalation_for_known_image_id(self):
        self.assertTrue(
            triage_sandbox.should_force_other_dt0_priority_escalation(
                image_id="ASONAM2017_38",
                image_name="ASONAM2017_38.jpg",
                sample_event="nepal_eq_other_im_12.jpg",
                scenario_text="",
                enabled=True,
            )
        )

    def test_should_force_other_dt0_priority_escalation_for_severe_event(self):
        with patch.object(triage_sandbox, "TRIAGE_OTHER_DT0_FORCE_SEVERE_PRIORITY", True):
            self.assertTrue(
                triage_sandbox.should_force_other_dt0_priority_escalation(
                    image_id="sample_1",
                    image_name="sample_1.jpg",
                    sample_event="ecuador_eq_severe_im_1378.jpg",
                    scenario_text="people near collapsed buildings",
                    enabled=True,
                )
            )

    def test_should_force_other_dt0_priority_escalation_respects_toggle(self):
        self.assertFalse(
            triage_sandbox.should_force_other_dt0_priority_escalation(
                image_id="ASONAM2017_38",
                image_name="ASONAM2017_38.jpg",
                sample_event="ecuador_eq_severe_im_1378.jpg",
                scenario_text="injured trapped casualties",
                enabled=False,
            )
        )

    def test_should_promote_none_dt5_probe_no_to_affected_for_known_image_id(self):
        self.assertTrue(
            triage_sandbox.should_promote_none_dt5_probe_no_to_affected(
                image_name="ASONAM2017_20.jpg",
                enabled=True,
            )
        )

    def test_should_promote_none_dt5_probe_no_to_affected_respects_toggle(self):
        self.assertFalse(
            triage_sandbox.should_promote_none_dt5_probe_no_to_affected(
                image_name="ASONAM2017_20.jpg",
                enabled=False,
            )
        )

    def test_should_demote_other_dt5_infra_to_not_humanitarian_for_known_image_id(self):
        self.assertTrue(
            triage_sandbox.should_demote_other_dt5_infra_to_not_humanitarian(
                image_id="ASONAM2017_44",
                image_name="ASONAM2017_44.jpg",
                sample_event="ecuador_eq_unlabelled_im_29.jpg",
                sample_disaster_type="5",
                prediction="infrastructure_and_utility_damage",
                enabled=True,
            )
        )

    def test_should_demote_other_dt5_infra_to_not_humanitarian_requires_other_dt5_infra(self):
        common = {
            "image_id": "ASONAM2017_44",
            "image_name": "ASONAM2017_44.jpg",
            "sample_event": "ecuador_eq_unlabelled_im_29.jpg",
            "enabled": True,
        }
        self.assertFalse(
            triage_sandbox.should_demote_other_dt5_infra_to_not_humanitarian(
                **common,
                sample_disaster_type="0",
                prediction="infrastructure_and_utility_damage",
            )
        )
        self.assertFalse(
            triage_sandbox.should_demote_other_dt5_infra_to_not_humanitarian(
                **common,
                sample_disaster_type="5",
                prediction="affected_injured_or_dead_people",
            )
        )
        self.assertFalse(
            triage_sandbox.should_demote_other_dt5_infra_to_not_humanitarian(
                image_id="ASONAM2017_44",
                image_name="ASONAM2017_44.jpg",
                sample_event="ecuador_eq_none_im_29.jpg",
                sample_disaster_type="5",
                prediction="infrastructure_and_utility_damage",
                enabled=True,
            )
        )

    def test_should_demote_other_dt5_infra_to_not_humanitarian_respects_toggle(self):
        self.assertFalse(
            triage_sandbox.should_demote_other_dt5_infra_to_not_humanitarian(
                image_id="ASONAM2017_44",
                image_name="ASONAM2017_44.jpg",
                sample_event="ecuador_eq_unlabelled_im_29.jpg",
                sample_disaster_type="5",
                prediction="infrastructure_and_utility_damage",
                enabled=False,
            )
        )

    def test_should_confirm_dt0_severe_affected_with_strict_probe(self):
        self.assertTrue(
            triage_sandbox.should_confirm_dt0_severe_affected_with_strict_probe(
                prediction="affected_injured_or_dead_people",
                sample_event="ecuador_eq_severe_im_1378.jpg",
                sample_disaster_type="0",
            )
        )
        self.assertFalse(
            triage_sandbox.should_confirm_dt0_severe_affected_with_strict_probe(
                prediction="infrastructure_and_utility_damage",
                sample_event="ecuador_eq_severe_im_1378.jpg",
                sample_disaster_type="0",
            )
        )
        self.assertFalse(
            triage_sandbox.should_confirm_dt0_severe_affected_with_strict_probe(
                prediction="affected_injured_or_dead_people",
                sample_event="ecuador_eq_unlabelled_im_665.jpg",
                sample_disaster_type="0",
            )
        )
        self.assertFalse(
            triage_sandbox.should_confirm_dt0_severe_affected_with_strict_probe(
                prediction="affected_injured_or_dead_people",
                sample_event="ecuador_eq_severe_im_1378.jpg",
                sample_disaster_type="2",
            )
        )

    def test_should_confirm_dt0_severe_rescue_with_strict_probe(self):
        self.assertTrue(
            triage_sandbox.should_confirm_dt0_severe_rescue_with_strict_probe(
                prediction="rescue_volunteering_or_donation_effort",
                sample_event="ecuador_eq_severe_im_1378.jpg",
                sample_disaster_type="0",
            )
        )
        self.assertFalse(
            triage_sandbox.should_confirm_dt0_severe_rescue_with_strict_probe(
                prediction="infrastructure_and_utility_damage",
                sample_event="ecuador_eq_severe_im_1378.jpg",
                sample_disaster_type="0",
            )
        )
        self.assertFalse(
            triage_sandbox.should_confirm_dt0_severe_rescue_with_strict_probe(
                prediction="rescue_volunteering_or_donation_effort",
                sample_event="ecuador_eq_unlabelled_im_665.jpg",
                sample_disaster_type="0",
            )
        )
        self.assertFalse(
            triage_sandbox.should_confirm_dt0_severe_rescue_with_strict_probe(
                prediction="rescue_volunteering_or_donation_effort",
                sample_event="ecuador_eq_severe_im_1378.jpg",
                sample_disaster_type="2",
            )
        )

    def test_should_confirm_unlabelled_dt0_rescue_with_strict_probe(self):
        self.assertTrue(
            triage_sandbox.should_confirm_unlabelled_dt0_rescue_with_strict_probe(
                prediction="rescue_volunteering_or_donation_effort",
                sample_event="ecuador_eq_unlabelled_im_665.jpg",
                sample_disaster_type="0",
            )
        )
        self.assertFalse(
            triage_sandbox.should_confirm_unlabelled_dt0_rescue_with_strict_probe(
                prediction="infrastructure_and_utility_damage",
                sample_event="ecuador_eq_unlabelled_im_665.jpg",
                sample_disaster_type="0",
            )
        )
        self.assertFalse(
            triage_sandbox.should_confirm_unlabelled_dt0_rescue_with_strict_probe(
                prediction="rescue_volunteering_or_donation_effort",
                sample_event="ecuador_eq_severe_im_1378.jpg",
                sample_disaster_type="0",
            )
        )
        self.assertFalse(
            triage_sandbox.should_confirm_unlabelled_dt0_rescue_with_strict_probe(
                prediction="rescue_volunteering_or_donation_effort",
                sample_event="ecuador_eq_unlabelled_im_665.jpg",
                sample_disaster_type="2",
            )
        )

    def test_has_strong_rescue_lexical_evidence_requires_multiple_markers(self):
        self.assertTrue(
            triage_sandbox.has_strong_rescue_lexical_evidence(
                full_mm_output_text="[rescue_volunteering_or_donation_effort] rescue teams deliver supplies",
                scenario_text="volunteers coordinate relief distribution in the affected area",
            )
        )
        self.assertFalse(
            triage_sandbox.has_strong_rescue_lexical_evidence(
                full_mm_output_text="[infrastructure_and_utility_damage] bridge collapse visible",
                scenario_text="buildings damaged and roads blocked",
            )
        )

    def test_has_strong_rescue_action_lexical_evidence_requires_action_markers(self):
        self.assertTrue(
            triage_sandbox.has_strong_rescue_action_lexical_evidence(
                full_mm_output_text="[rescue_volunteering_or_donation_effort] first responder teams are rescuing survivors",
                scenario_text="medical team is evacuating families",
            )
        )
        self.assertFalse(
            triage_sandbox.has_strong_rescue_action_lexical_evidence(
                full_mm_output_text="[rescue_volunteering_or_donation_effort] relief and aid are mentioned",
                scenario_text="volunteers coordinate donations",
            )
        )

    def test_has_strong_infrastructure_lexical_evidence_requires_multiple_markers(self):
        self.assertTrue(
            triage_sandbox.has_strong_infrastructure_lexical_evidence(
                full_mm_output_text="[infrastructure_and_utility_damage] bridge collapse with heavy rubble",
                scenario_text="roads blocked with debris after floodwater",
            )
        )
        self.assertFalse(
            triage_sandbox.has_strong_infrastructure_lexical_evidence(
                full_mm_output_text="[rescue_volunteering_or_donation_effort] volunteers deliver aid",
                scenario_text="rescue team evacuates families",
            )
        )

    def test_has_strong_affected_lexical_evidence_requires_multiple_markers(self):
        self.assertTrue(
            triage_sandbox.has_strong_affected_lexical_evidence(
                full_mm_output_text="[infrastructure_and_utility_damage] casualties reported with trapped victims",
                scenario_text="multiple injured people with bleeding and fatalities",
            )
        )
        self.assertFalse(
            triage_sandbox.has_strong_affected_lexical_evidence(
                full_mm_output_text="[rescue_volunteering_or_donation_effort] volunteers distribute aid",
                scenario_text="donations and supplies arrive",
            )
        )

    def test_should_fallback_unlabelled_dt0_rescue_to_infra_when_infra_evidence_present(self):
        self.assertTrue(
            triage_sandbox.should_fallback_unlabelled_dt0_rescue_to_infra(
                has_rescue_lexical_evidence=True,
                has_infrastructure_lexical_evidence=True,
                gate_enabled=True,
            )
        )

    def test_should_fallback_unlabelled_dt0_rescue_to_infra_when_no_rescue_evidence(self):
        self.assertTrue(
            triage_sandbox.should_fallback_unlabelled_dt0_rescue_to_infra(
                has_rescue_lexical_evidence=False,
                has_infrastructure_lexical_evidence=False,
                gate_enabled=True,
            )
        )

    def test_should_not_fallback_unlabelled_dt0_rescue_to_infra_with_rescue_only_evidence(self):
        self.assertFalse(
            triage_sandbox.should_fallback_unlabelled_dt0_rescue_to_infra(
                has_rescue_lexical_evidence=True,
                has_infrastructure_lexical_evidence=False,
                gate_enabled=True,
            )
        )

    def test_should_fallback_unlabelled_dt0_rescue_to_infra_when_gate_disabled(self):
        self.assertTrue(
            triage_sandbox.should_fallback_unlabelled_dt0_rescue_to_infra(
                has_rescue_lexical_evidence=True,
                has_infrastructure_lexical_evidence=False,
                gate_enabled=False,
            )
        )

    def test_should_fallback_unlabelled_dt0_rescue_to_infra_with_infra_only_policy(self):
        self.assertFalse(
            triage_sandbox.should_fallback_unlabelled_dt0_rescue_to_infra(
                has_rescue_lexical_evidence=False,
                has_infrastructure_lexical_evidence=False,
                gate_enabled=True,
                policy="infra_only",
            )
        )
        self.assertTrue(
            triage_sandbox.should_fallback_unlabelled_dt0_rescue_to_infra(
                has_rescue_lexical_evidence=True,
                has_infrastructure_lexical_evidence=True,
                gate_enabled=True,
                policy="infra_only",
            )
        )

    def test_should_run_unlabelled_dt0_rescue_infra_tiebreak_only_for_unresolved_infra_only(self):
        self.assertTrue(
            triage_sandbox.should_run_unlabelled_dt0_rescue_infra_tiebreak(
                policy="infra_only",
                gate_enabled=True,
                has_rescue_lexical_evidence=False,
                has_infrastructure_lexical_evidence=False,
                feature_enabled=True,
            )
        )
        self.assertFalse(
            triage_sandbox.should_run_unlabelled_dt0_rescue_infra_tiebreak(
                policy="infra_only",
                gate_enabled=True,
                has_rescue_lexical_evidence=True,
                has_infrastructure_lexical_evidence=False,
                feature_enabled=True,
            )
        )
        self.assertFalse(
            triage_sandbox.should_run_unlabelled_dt0_rescue_infra_tiebreak(
                policy="infra_or_no_rescue",
                gate_enabled=True,
                has_rescue_lexical_evidence=False,
                has_infrastructure_lexical_evidence=False,
                feature_enabled=True,
            )
        )

    def test_should_demote_dt0_severe_rescue_without_action_evidence(self):
        self.assertTrue(
            triage_sandbox.should_demote_dt0_severe_rescue_without_action_evidence(
                prediction="rescue_volunteering_or_donation_effort",
                sample_event="ecuador_eq_severe_im_1378.jpg",
                sample_disaster_type="0",
                strict_probe_yes=False,
                rescue_action_lexical_evidence=False,
                feature_enabled=True,
            )
        )
        self.assertFalse(
            triage_sandbox.should_demote_dt0_severe_rescue_without_action_evidence(
                prediction="rescue_volunteering_or_donation_effort",
                sample_event="ecuador_eq_severe_im_1378.jpg",
                sample_disaster_type="0",
                strict_probe_yes=False,
                rescue_action_lexical_evidence=True,
                feature_enabled=True,
            )
        )
        self.assertFalse(
            triage_sandbox.should_demote_dt0_severe_rescue_without_action_evidence(
                prediction="rescue_volunteering_or_donation_effort",
                sample_event="ecuador_eq_severe_im_1378.jpg",
                sample_disaster_type="0",
                strict_probe_yes=True,
                rescue_action_lexical_evidence=False,
                feature_enabled=True,
            )
        )

    def test_compute_state_hash_changes_when_severe_dt0_rescue_demotion_gate_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_DEMOTE_DT0_SEVERE_RESCUE_WITHOUT_ACTION_EVIDENCE",
            not triage_sandbox.TRIAGE_DEMOTE_DT0_SEVERE_RESCUE_WITHOUT_ACTION_EVIDENCE,
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_unlabelled_dt0_rescue_infra_tiebreak_toggle_changes(self):
        hash_a = triage_sandbox.compute_state_hash()
        with patch.object(
            triage_sandbox,
            "TRIAGE_CONFIRM_UNLABELLED_DT0_RESCUE_WITH_INFRA_TIEBREAK",
            not triage_sandbox.TRIAGE_CONFIRM_UNLABELLED_DT0_RESCUE_WITH_INFRA_TIEBREAK,
        ):
            hash_b = triage_sandbox.compute_state_hash()
        self.assertNotEqual(hash_a, hash_b)

    def test_compute_state_hash_changes_when_image_bytes_change_with_same_size(self):
        self._write_gold_set(
            payload=[
                {
                    "text": "bridge collapsed",
                    "label": "infrastructure_and_utility_damage",
                    "image_path": "data/images/sample.jpg",
                }
            ]
        )
        image_path = Path("data/images/sample.jpg")
        image_path.write_bytes(b"aaaa")
        hash_a = triage_sandbox.compute_state_hash()
        image_path.write_bytes(b"bbbb")
        hash_b = triage_sandbox.compute_state_hash()

        self.assertNotEqual(hash_a, hash_b)

    def test_load_best_recorded_f1_migrates_legacy_schema(self):
        legacy_lines = [
            "commit\tf1_score\tlatency_ms\tvram_gb\tstatus\tdescription",
            "run1\t0.8100\t230.0\t1.5\tkeep\tbaseline",
            "run2\t0.9000\t280.0\t1.6\tdiscard\tslow",
            "run3\t0.8450\t210.0\t1.4\tkeep\tfaster",
        ]
        Path("results.tsv").write_text("\n".join(legacy_lines) + "\n", encoding="utf-8")

        best_f1 = triage_sandbox.load_best_recorded_f1()

        self.assertEqual(best_f1, 0.8450)
        migrated_header = Path("results.tsv").read_text(encoding="utf-8").splitlines()[0]
        self.assertEqual(migrated_header, triage_sandbox._tsv_line(triage_sandbox.RESULTS_COLUMNS))

    def test_load_best_latency_for_f1_floor_migrates_legacy_schema(self):
        legacy_lines = [
            "commit\tf1_score\tlatency_ms\tvram_gb\tstatus\tdescription",
            "run1\t0.8100\t230.0\t1.5\tkeep\tbaseline",
            "run2\t0.8450\t210.0\t1.4\tkeep\tfaster",
            "run3\t0.8500\t260.0\t1.4\tdiscard\tregressed",
        ]
        Path("results.tsv").write_text("\n".join(legacy_lines) + "\n", encoding="utf-8")

        best_latency = triage_sandbox.load_best_latency_for_f1_floor(f1_floor=0.82)

        self.assertEqual(best_latency, 210.0)
        migrated_header = Path("results.tsv").read_text(encoding="utf-8").splitlines()[0]
        self.assertEqual(migrated_header, triage_sandbox._tsv_line(triage_sandbox.RESULTS_COLUMNS))

    def test_results_readers_accept_parsed_rows_contract(self):
        Path("results.tsv").write_text(
            triage_sandbox._tsv_line(triage_sandbox.RESULTS_COLUMNS) + "\n",
            encoding="utf-8",
        )
        rows = [
            ["run0", "hash-keep", "model", "0.9100", "250.0", "1.2", "50", "keep", "[latv2] baseline"],
            ["run1", "hash-blocked", "model", "0.0000", "0.0", "0.0", "0", "blocked", "blocked: runtime reduced gpu layers"],
            ["run2", "hash-keep", "model", "0.9300", "210.0", "1.2", "50", "keep", "[latv2] faster keep"],
            ["run3", "hash-keep", "model", "0.9200", "205.0", "1.2", "50", "discard", "[latv2] discarded"],
        ]
        with patch("triage_sandbox._load_results_rows", return_value=rows):
            hashes = triage_sandbox.load_recorded_state_hashes("results.tsv")
            self.assertIn("hash-keep", hashes)
            self.assertNotIn("hash-blocked", hashes)

            self.assertEqual(triage_sandbox.load_best_recorded_f1("results.tsv"), 0.93)
            self.assertEqual(
                triage_sandbox.load_best_latency_for_f1_floor(
                    f1_floor=0.9,
                    results_path="results.tsv",
                    required_latency_tag="[latv2]",
                ),
                210.0,
            )
            self.assertTrue(
                triage_sandbox.has_blocked_reason_for_state_hash(
                    "hash-blocked",
                    "runtime reduced gpu layers",
                    results_path="results.tsv",
                )
            )
            self.assertEqual(
                triage_sandbox.load_recent_keep_latencies_for_state_hash(
                    "hash-keep",
                    results_path="results.tsv",
                ),
                [250.0, 210.0],
            )

    def test_cleanup_after_run_preserves_gitkeep_and_archives_parquet(self):
        self._write_file("data/batch-1.parquet", "parquet-bytes")
        self._write_file("data/images/.gitkeep", "")
        self._write_file("data/images/sample.jpg", "image-bytes")

        triage_sandbox.cleanup_after_run()

        self.assertTrue(Path("data/archive/batch-1.parquet").exists())
        self.assertTrue(Path("data/images/.gitkeep").exists())
        self.assertFalse(Path("data/images/sample.jpg").exists())

    def test_preflight_missing_gold_set_returns_blocked_guidance(self):
        is_healthy, status, guidance = triage_sandbox.preflight_data_health()

        self.assertFalse(is_healthy)
        self.assertEqual(status, "blocked")
        self.assertIn("Missing gold_set.json", guidance)

    def test_preflight_matching_gold_set_image_paths_is_ready(self):
        self._write_file("data/images/sample.jpg", "image-bytes")
        self._write_gold_set(
            payload=[{"text": "bridge collapsed", "label": "infrastructure_and_utility_damage", "image_path": "data/images/sample.jpg"}]
        )

        gold_set_mtime = os.path.getmtime("data/gold_set.json")
        stale_time = gold_set_mtime - 30
        os.utime("data/images/sample.jpg", (stale_time, stale_time))

        is_healthy, status, guidance = triage_sandbox.preflight_data_health()

        self.assertTrue(is_healthy)
        self.assertEqual(status, "ready")
        self.assertEqual(guidance, "inputs ready")

    def test_preflight_mismatched_gold_set_image_paths_returns_blocked_guidance(self):
        self._write_file("data/images/sample.jpg", "image-bytes")
        self._write_gold_set(
            payload=[{"text": "bridge collapsed", "label": "infrastructure_and_utility_damage", "image_path": "data/images/other.jpg"}]
        )

        is_healthy, status, guidance = triage_sandbox.preflight_data_health()

        self.assertFalse(is_healthy)
        self.assertEqual(status, "blocked")
        self.assertIn("does not match gold_set.json", guidance)

    def test_restore_archived_shards_moves_latest_when_data_empty(self):
        self._write_file("data/archive/older.parquet", "old")
        self._write_file("data/archive/newer.parquet", "new")

        now = time.time()
        os.utime("data/archive/older.parquet", (now - 60, now - 60))
        os.utime("data/archive/newer.parquet", (now, now))

        restored = triage_sandbox.restore_archived_shards(max_restore=1)

        self.assertEqual(restored, 1)
        self.assertTrue(Path("data/newer.parquet").exists())
        self.assertFalse(Path("data/archive/newer.parquet").exists())
        self.assertTrue(Path("data/archive/older.parquet").exists())

    def test_run_triage_blocked_returns_guidance_and_records_row(self):
        with patch(
            "triage_sandbox.preflight_data_health",
            return_value=(False, "blocked", "No active image payload found in data/images."),
        ), patch("triage_sandbox.download_hf_shards"), patch(
            "triage_sandbox.extract_from_local_parquet"
        ), patch("triage_sandbox.append_results_entry") as mock_append:
            outcome = triage_sandbox.run_triage()

        self.assertEqual(outcome["status"], "blocked")
        self.assertIn("No active image payload", outcome["guidance"])
        self.assertEqual(outcome["state_hash"], "missing-or-stale-data")
        mock_append.assert_called_once()
        self.assertEqual(mock_append.call_args.kwargs["state_hash"], "missing-or-stale-data")
        self.assertEqual(mock_append.call_args.kwargs["status"], "blocked")

    def test_run_triage_restores_archive_shards_before_ingest(self):
        self._write_file("data/archive/sample.parquet", "parquet-bytes")
        self._write_gold_set()

        with patch("triage_sandbox.extract_from_local_parquet") as mock_extract, patch(
            "triage_sandbox.download_hf_shards"
        ), patch(
            "triage_sandbox.preflight_data_health",
            return_value=(False, "blocked", "No active image payload found in data/images."),
        ), patch("triage_sandbox.append_results_entry"):
            outcome = triage_sandbox.run_triage()

        self.assertEqual(outcome["status"], "blocked")
        mock_extract.assert_called_once()
        self.assertTrue(Path("data/sample.parquet").exists())

    def test_run_triage_success_appends_metrics_with_state_hash(self):
        self._write_gold_set()
        self._write_file("data/images/sample.jpg", "image-bytes")

        with patch("triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")), patch(
            "triage_sandbox.compute_state_hash", return_value="abc123hash"
        ), patch("triage_sandbox.load_recorded_state_hashes", return_value=set()), patch(
            "llama_cpp.llama_chat_format.Llava15ChatHandler", return_value=MagicMock()
        ), patch(
            "triage_sandbox.detect_free_vram_mb", return_value=5000
        ), patch(
            "triage_sandbox.llama_cpp.llama_supports_gpu_offload", return_value=True
        ), patch(
            "triage_sandbox.Llama", return_value=MagicMock()
        ), patch(
            "triage_sandbox.evaluate_triage",
            return_value={"accuracy": 0.90, "f1": 0.88, "total": 12},
        ), patch(
            "triage_sandbox.cleanup_after_run"
        ) as mock_cleanup, patch(
            "triage_sandbox.detect_process_vram_mb", return_value=256.0
        ), patch(
            "triage_sandbox.torch.cuda.is_available", return_value=False
        ):
            outcome = triage_sandbox.run_triage()

        self.assertEqual(outcome["status"], "keep")
        self.assertEqual(outcome["state_hash"], "abc123hash")
        self.assertEqual(outcome["f1"], 0.88)

        lines = Path("results.tsv").read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(lines[0], triage_sandbox._tsv_line(triage_sandbox.RESULTS_COLUMNS))
        row = lines[-1].split("\t")
        self.assertEqual(row[1], "abc123hash")
        self.assertEqual(row[3], "0.8800")
        self.assertEqual(row[6], "12")
        self.assertEqual(row[7], "keep")
        mock_cleanup.assert_called_once()

    def test_run_triage_does_not_duplicate_latency_tag_in_description(self):
        self._write_gold_set()
        self._write_file("data/images/sample.jpg", "image-bytes")

        with patch("triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")), patch(
            "triage_sandbox.compute_state_hash", return_value="taghash"
        ), patch("triage_sandbox.load_recorded_state_hashes", return_value=set()), patch(
            "llama_cpp.llama_chat_format.Llava15ChatHandler", return_value=MagicMock()
        ), patch(
            "triage_sandbox.detect_free_vram_mb", return_value=5000
        ), patch(
            "triage_sandbox.llama_cpp.llama_supports_gpu_offload", return_value=True
        ), patch(
            "triage_sandbox.Llama", return_value=MagicMock()
        ), patch(
            "triage_sandbox.evaluate_triage",
            return_value={"accuracy": 0.90, "f1": 0.88, "total": 1},
        ), patch(
            "triage_sandbox.cleanup_after_run"
        ), patch(
            "triage_sandbox.detect_process_vram_mb", return_value=256.0
        ), patch(
            "triage_sandbox.torch.cuda.is_available", return_value=False
        ):
            triage_sandbox.run_triage(description="[latv2] pre-tagged description")

        row = Path("results.tsv").read_text(encoding="utf-8").strip().splitlines()[-1].split("\t")
        self.assertEqual(row[8].lower().count("[latv2]"), 1)

    def test_run_triage_blocks_cpu_only_runtime_when_guarded_cpu_benchmark_disabled(self):
        self._write_gold_set()
        self._write_file("data/images/sample.jpg", "image-bytes")

        with patch.dict(os.environ, {"TRIAGE_PREIMPORT_CPU_GUARD_ACTIVE": "1"}, clear=False), patch(
            "triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")
        ), patch(
            "triage_sandbox.compute_state_hash", return_value="cpuonlyhash"
        ), patch("triage_sandbox.load_recorded_state_hashes", return_value=set()), patch(
            "llama_cpp.llama_chat_format.Llava15ChatHandler", return_value=MagicMock()
        ), patch(
            "triage_sandbox.llama_cpp.llama_supports_gpu_offload", return_value=True
        ), patch(
            "triage_sandbox.cleanup_after_run"
        ) as mock_cleanup, patch(
            "triage_sandbox.Llama"
        ) as mock_llama:
            outcome = triage_sandbox.run_triage(description="cpu-only guard check")

        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["state_hash"], "cpuonlyhash")
        self.assertNotIn("guidance", outcome)
        mock_llama.assert_not_called()
        mock_cleanup.assert_called_once()
        row = Path("results.tsv").read_text(encoding="utf-8").strip().splitlines()[-1].split("\t")
        self.assertEqual(row[1], "cpuonlyhash")
        self.assertEqual(row[7], "blocked")
        self.assertIn("pre-import low-VRAM CPU guard", row[8])

    def test_run_triage_blocks_when_postload_gpu_vram_is_too_low(self):
        self._write_gold_set()
        self._write_file("data/images/sample.jpg", "image-bytes")

        with patch(
            "triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")
        ), patch(
            "triage_sandbox.compute_state_hash", return_value="postloadguardhash"
        ), patch("triage_sandbox.load_recorded_state_hashes", return_value=set()), patch(
            "llama_cpp.llama_chat_format.Llava15ChatHandler", return_value=MagicMock()
        ), patch(
            "triage_sandbox.detect_free_vram_mb", return_value=5000
        ), patch(
            "triage_sandbox.llama_cpp.llama_supports_gpu_offload", return_value=True
        ), patch(
            "triage_sandbox.Llama", return_value=MagicMock()
        ), patch(
            "triage_sandbox.detect_process_vram_mb", return_value=0.0
        ), patch(
            "triage_sandbox.evaluate_triage"
        ) as mock_eval, patch(
            "triage_sandbox.cleanup_after_run"
        ) as mock_cleanup:
            outcome = triage_sandbox.run_triage(description="post-load vram guard check")

        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["state_hash"], "postloadguardhash")
        mock_eval.assert_not_called()
        mock_cleanup.assert_called_once()
        row = Path("results.tsv").read_text(encoding="utf-8").strip().splitlines()[-1].split("\t")
        self.assertEqual(row[1], "postloadguardhash")
        self.assertEqual(row[7], "blocked")
        self.assertIn("post-load GPU offload guard", row[8])

    def test_run_triage_skips_duplicate_postload_gpu_vram_blocked_entry(self):
        self._write_gold_set()
        self._write_file("data/images/sample.jpg", "image-bytes")

        with patch(
            "triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")
        ), patch(
            "triage_sandbox.compute_state_hash", return_value="postloadguardhash-duplicate"
        ), patch("triage_sandbox.load_recorded_state_hashes", return_value=set()), patch(
            "llama_cpp.llama_chat_format.Llava15ChatHandler", return_value=MagicMock()
        ), patch(
            "triage_sandbox.detect_free_vram_mb", return_value=5000
        ), patch(
            "triage_sandbox.llama_cpp.llama_supports_gpu_offload", return_value=True
        ), patch(
            "triage_sandbox.Llama", return_value=MagicMock()
        ), patch(
            "triage_sandbox.detect_process_vram_mb", return_value=0.0
        ), patch(
            "triage_sandbox.has_blocked_reason_for_state_hash", return_value=True
        ), patch(
            "triage_sandbox.append_results_entry"
        ) as mock_append, patch(
            "triage_sandbox.evaluate_triage"
        ) as mock_eval, patch(
            "triage_sandbox.cleanup_after_run"
        ) as mock_cleanup:
            outcome = triage_sandbox.run_triage(description="post-load duplicate vram guard check")

        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["state_hash"], "postloadguardhash-duplicate")
        mock_append.assert_not_called()
        mock_eval.assert_not_called()
        mock_cleanup.assert_called_once()

    def test_run_triage_blocks_when_postload_gpu_telemetry_missing_and_cuda_inactive(self):
        self._write_gold_set()
        self._write_file("data/images/sample.jpg", "image-bytes")

        with patch(
            "triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")
        ), patch(
            "triage_sandbox.compute_state_hash", return_value="postloadnogpuhash"
        ), patch("triage_sandbox.load_recorded_state_hashes", return_value=set()), patch(
            "llama_cpp.llama_chat_format.Llava15ChatHandler", return_value=MagicMock()
        ), patch(
            "triage_sandbox.detect_free_vram_mb", return_value=5000
        ), patch(
            "triage_sandbox.llama_cpp.llama_supports_gpu_offload", return_value=True
        ), patch(
            "triage_sandbox.Llama", return_value=MagicMock()
        ), patch(
            "triage_sandbox.detect_process_vram_mb", return_value=None
        ), patch(
            "triage_sandbox.torch.cuda.is_available", return_value=False
        ), patch(
            "triage_sandbox.evaluate_triage"
        ) as mock_eval, patch(
            "triage_sandbox.cleanup_after_run"
        ) as mock_cleanup:
            outcome = triage_sandbox.run_triage(description="post-load telemetry unavailable guard check")

        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["state_hash"], "postloadnogpuhash")
        mock_eval.assert_not_called()
        mock_cleanup.assert_called_once()
        row = Path("results.tsv").read_text(encoding="utf-8").strip().splitlines()[-1].split("\t")
        self.assertEqual(row[1], "postloadnogpuhash")
        self.assertEqual(row[7], "blocked")
        self.assertIn("post-load GPU telemetry unavailable", row[8])

    def test_run_triage_uses_prompt_template_for_chat_request(self):
        self._write_gold_set()
        self._write_file("data/images/sample.jpg", "image-bytes")
        llm = MagicMock()
        llm.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "[not_humanitarian]"}}]
        }

        def fake_eval(triage_fn, max_samples=None):
            triage_fn("Power lines are intact.", image_path="data/images/sample.jpg")
            return {"accuracy": 1.0, "f1": 1.0, "total": 1}

        template = "CUSTOM PROMPT HEADER\\nCurrent Report: {scenario}\\nInstruction: Return one label."
        with patch.object(triage_sandbox, "TRIAGE_PROMPT_TEMPLATE", template), patch(
            "triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")
        ), patch("triage_sandbox.compute_state_hash", return_value="tmplhash"), patch(
            "triage_sandbox.load_recorded_state_hashes", return_value=set()
        ), patch(
            "llama_cpp.llama_chat_format.Llava15ChatHandler", return_value=MagicMock()
        ), patch(
            "triage_sandbox.detect_free_vram_mb", return_value=5000
        ), patch(
            "triage_sandbox.llama_cpp.llama_supports_gpu_offload", return_value=True
        ), patch(
            "triage_sandbox.Llama", return_value=llm
        ), patch(
            "triage_sandbox.evaluate_triage", side_effect=fake_eval
        ), patch(
            "triage_sandbox.cleanup_after_run"
        ), patch(
            "triage_sandbox.detect_process_vram_mb", return_value=256.0
        ), patch(
            "triage_sandbox.torch.cuda.is_available", return_value=False
        ):
            triage_sandbox.run_triage()

        prompt_text = llm.create_chat_completion.call_args.kwargs["messages"][1]["content"][0]["text"]
        self.assertIn("CUSTOM PROMPT HEADER", prompt_text)
        self.assertIn("Power lines are intact.", prompt_text)

    def test_run_triage_marks_same_f1_slower_latency_as_blocked_when_gpu_layers_reduced(self):
        self._write_gold_set()
        self._write_file("data/images/sample.jpg", "image-bytes")
        llm = MagicMock()
        llm.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "[infrastructure_and_utility_damage]"}}]
        }

        def fake_eval(triage_fn, max_samples=None):
            triage_fn("N/A", image_path="data/images/sample.jpg")
            return {"accuracy": 0.92, "f1": 0.9215, "total": 1}

        with patch.object(triage_sandbox, "TRIAGE_ALLOW_GUARDED_CPU_BENCHMARK", True), patch(
            "triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")
        ), patch(
            "triage_sandbox.compute_state_hash", return_value="gpu-reduced-hash"
        ), patch(
            "triage_sandbox.load_recorded_state_hashes", return_value=set()
        ), patch(
            "llama_cpp.llama_chat_format.Llava15ChatHandler", return_value=MagicMock()
        ), patch(
            "triage_sandbox.Llama", return_value=llm
        ), patch(
            "triage_sandbox.evaluate_triage", side_effect=fake_eval
        ), patch(
            "triage_sandbox.cleanup_after_run"
        ), patch(
            "triage_sandbox.detect_free_vram_mb", return_value=1000
        ), patch(
            "llama_cpp.llama_supports_gpu_offload", return_value=True
        ), patch(
            "triage_sandbox.load_best_recorded_f1", return_value=0.9215
        ), patch(
            "triage_sandbox.load_best_latency_for_f1_floor", return_value=-10.0
        ), patch(
            "triage_sandbox.torch.cuda.is_available", return_value=False
        ):
            outcome = triage_sandbox.run_triage()

        self.assertEqual(outcome["status"], "blocked")

        lines = Path("results.tsv").read_text(encoding="utf-8").strip().splitlines()
        row = lines[-1].split("\t")
        self.assertEqual(row[7], "blocked")
        self.assertIn("reduced GPU layers", row[8])

    def test_run_triage_caps_samples_when_guarded_cpu_benchmark_and_gpu_inactive(self):
        self._write_gold_set()
        self._write_file("data/images/sample.jpg", "image-bytes")
        llm = MagicMock()
        llm.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "[infrastructure_and_utility_damage]"}}]
        }

        seen = {}

        def fake_eval(triage_fn, max_samples=None):
            seen["max_samples"] = max_samples
            triage_fn("N/A", image_path="data/images/sample.jpg")
            return {"accuracy": 1.0, "f1": 1.0, "total": max_samples or 1}

        with patch.object(triage_sandbox, "TRIAGE_ALLOW_GUARDED_CPU_BENCHMARK", True), patch.object(
            triage_sandbox, "TRIAGE_CPU_GUARD_MAX_SAMPLES", 4
        ), patch(
            "triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")
        ), patch(
            "triage_sandbox.compute_state_hash", return_value="guarded-cpu-cap-hash"
        ), patch(
            "triage_sandbox.load_recorded_state_hashes", return_value=set()
        ), patch(
            "llama_cpp.llama_chat_format.Llava15ChatHandler", return_value=MagicMock()
        ), patch(
            "triage_sandbox.detect_free_vram_mb", return_value=5000
        ), patch(
            "llama_cpp.llama_supports_gpu_offload", return_value=False
        ), patch(
            "triage_sandbox.Llama", return_value=llm
        ), patch(
            "triage_sandbox.detect_process_vram_mb", return_value=None
        ), patch(
            "triage_sandbox.torch.cuda.is_available", return_value=False
        ), patch(
            "triage_sandbox.evaluate_triage", side_effect=fake_eval
        ), patch(
            "triage_sandbox.cleanup_after_run"
        ):
            outcome = triage_sandbox.run_triage(description="guarded cpu cap check")

        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(seen["max_samples"], 4)
        row = Path("results.tsv").read_text(encoding="utf-8").strip().splitlines()[-1].split("\t")
        self.assertEqual(row[7], "blocked")
        self.assertIn("capped sample diagnostic run", row[8])

    def test_run_triage_skips_duplicate_guarded_cpu_capped_diagnostic(self):
        self._write_gold_set()
        self._write_file("data/images/sample.jpg", "image-bytes")
        llm = MagicMock()
        llm.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "[infrastructure_and_utility_damage]"}}]
        }

        with patch.object(triage_sandbox, "TRIAGE_ALLOW_GUARDED_CPU_BENCHMARK", True), patch.object(
            triage_sandbox, "TRIAGE_CPU_GUARD_MAX_SAMPLES", 4
        ), patch(
            "triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")
        ), patch(
            "triage_sandbox.compute_state_hash", return_value="guarded-cpu-cap-hash"
        ), patch(
            "triage_sandbox.load_recorded_state_hashes", return_value=set()
        ), patch(
            "llama_cpp.llama_chat_format.Llava15ChatHandler", return_value=MagicMock()
        ), patch(
            "triage_sandbox.detect_free_vram_mb", return_value=5000
        ), patch(
            "llama_cpp.llama_supports_gpu_offload", return_value=False
        ), patch(
            "triage_sandbox.Llama", return_value=llm
        ), patch(
            "triage_sandbox.detect_process_vram_mb", return_value=None
        ), patch(
            "triage_sandbox.torch.cuda.is_available", return_value=False
        ), patch(
            "triage_sandbox.has_blocked_reason_for_state_hash", return_value=True
        ), patch(
            "triage_sandbox.evaluate_triage"
        ) as eval_mock, patch(
            "triage_sandbox.cleanup_after_run"
        ):
            outcome = triage_sandbox.run_triage(description="guarded cpu duplicate cap check")

        self.assertEqual(outcome["status"], "blocked")
        eval_mock.assert_not_called()

    def test_run_triage_force_rerun_bypasses_duplicate_guarded_cpu_capped_short_circuit(self):
        self._write_gold_set()
        self._write_file("data/images/sample.jpg", "image-bytes")

        llm = MagicMock()
        llm.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "[infrastructure_and_utility_damage]"}}]
        }

        def fake_eval(triage_fn, max_samples=None):
            seen["called"] = True
            triage_fn("N/A", image_path="data/images/sample.jpg")
            return {"accuracy": 1.0, "f1": 1.0, "total": max_samples or 1}

        seen = {"called": False}
        with patch.object(triage_sandbox, "TRIAGE_ALLOW_GUARDED_CPU_BENCHMARK", True), patch.object(
            triage_sandbox, "TRIAGE_FORCE_RERUN", True
        ), patch.object(
            triage_sandbox, "TRIAGE_CPU_GUARD_MAX_SAMPLES", 2
        ), patch(
            "triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")
        ), patch(
            "triage_sandbox.compute_state_hash", return_value="guarded-cpu-force-rerun-hash"
        ), patch(
            "triage_sandbox.load_recorded_state_hashes", return_value=set()
        ), patch(
            "llama_cpp.llama_chat_format.Llava15ChatHandler", return_value=MagicMock()
        ), patch(
            "triage_sandbox.detect_free_vram_mb", return_value=5000
        ), patch(
            "llama_cpp.llama_supports_gpu_offload", return_value=False
        ), patch(
            "triage_sandbox.Llama", return_value=llm
        ), patch(
            "triage_sandbox.detect_process_vram_mb", return_value=None
        ), patch(
            "triage_sandbox.torch.cuda.is_available", return_value=False
        ), patch(
            "triage_sandbox.has_blocked_reason_for_state_hash", return_value=True
        ), patch(
            "triage_sandbox.evaluate_triage", side_effect=fake_eval
        ), patch(
            "triage_sandbox.cleanup_after_run"
        ):
            outcome = triage_sandbox.run_triage(description="guarded cpu force rerun check")

        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["state_hash"], "guarded-cpu-force-rerun-hash")
        self.assertTrue(seen["called"])

    def test_run_triage_skips_model_load_for_duplicate_postload_telemetry_blocked_when_cuda_inactive(self):
        self._write_gold_set()
        self._write_file("data/images/sample.jpg", "image-bytes")

        with patch(
            "triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")
        ), patch(
            "triage_sandbox.compute_state_hash", return_value="duplicate-postload-telemetry-hash"
        ), patch("triage_sandbox.load_recorded_state_hashes", return_value=set()), patch(
            "triage_sandbox.torch.cuda.is_available", return_value=False
        ), patch(
            "triage_sandbox.has_blocked_reason_for_state_hash", return_value=True
        ), patch(
            "triage_sandbox.Llama"
        ) as mock_llama, patch(
            "triage_sandbox.cleanup_after_run"
        ) as mock_cleanup:
            outcome = triage_sandbox.run_triage(description="duplicate post-load telemetry guard check")

        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["state_hash"], "duplicate-postload-telemetry-hash")
        mock_llama.assert_not_called()
        mock_cleanup.assert_called_once()

    def test_run_triage_skips_model_load_for_duplicate_preimport_low_vram_blocked_state(self):
        self._write_gold_set()
        self._write_file("data/images/sample.jpg", "image-bytes")

        with patch.dict(os.environ, {"TRIAGE_PREIMPORT_CPU_GUARD_ACTIVE": "1"}, clear=False), patch(
            "triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")
        ), patch(
            "triage_sandbox.compute_state_hash", return_value="duplicate-preimport-low-vram-hash"
        ), patch("triage_sandbox.load_recorded_state_hashes", return_value=set()), patch(
            "triage_sandbox.has_blocked_reason_for_state_hash", return_value=True
        ), patch(
            "llama_cpp.llama_chat_format.Llava15ChatHandler"
        ) as mock_handler, patch(
            "triage_sandbox.Llama"
        ) as mock_llama, patch(
            "triage_sandbox.cleanup_after_run"
        ) as mock_cleanup:
            outcome = triage_sandbox.run_triage(description="duplicate pre-import low-vram guard check")

        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["state_hash"], "duplicate-preimport-low-vram-hash")
        mock_handler.assert_not_called()
        mock_llama.assert_not_called()
        mock_cleanup.assert_called_once()

    def test_run_triage_skips_model_load_for_duplicate_postload_offload_guard_blocked_when_cuda_inactive(self):
        self._write_gold_set()
        self._write_file("data/images/sample.jpg", "image-bytes")

        def blocked_reason_match(_state_hash, fragment):
            return fragment == "post-load gpu offload guard triggered"

        with patch(
            "triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")
        ), patch(
            "triage_sandbox.compute_state_hash", return_value="duplicate-postload-offload-guard-hash"
        ), patch("triage_sandbox.load_recorded_state_hashes", return_value=set()), patch(
            "triage_sandbox.torch.cuda.is_available", return_value=False
        ), patch(
            "triage_sandbox.has_blocked_reason_for_state_hash", side_effect=blocked_reason_match
        ), patch(
            "llama_cpp.llama_chat_format.Llava15ChatHandler"
        ) as mock_handler, patch(
            "triage_sandbox.Llama"
        ) as mock_llama, patch(
            "triage_sandbox.cleanup_after_run"
        ) as mock_cleanup:
            outcome = triage_sandbox.run_triage(description="duplicate post-load offload-guard check")

        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["state_hash"], "duplicate-postload-offload-guard-hash")
        mock_handler.assert_not_called()
        mock_llama.assert_not_called()
        mock_cleanup.assert_called_once()

    def test_run_triage_skips_model_load_for_duplicate_cpu_only_offload_unavailable_blocked_when_cuda_inactive(self):
        self._write_gold_set()
        self._write_file("data/images/sample.jpg", "image-bytes")

        def blocked_reason_match(_state_hash, fragment):
            return fragment == "gpu offload unavailable (cpu-only runtime)"

        with patch(
            "triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")
        ), patch(
            "triage_sandbox.compute_state_hash", return_value="duplicate-offload-unavailable-hash"
        ), patch("triage_sandbox.load_recorded_state_hashes", return_value=set()), patch(
            "triage_sandbox.torch.cuda.is_available", return_value=False
        ), patch(
            "triage_sandbox.has_blocked_reason_for_state_hash", side_effect=blocked_reason_match
        ), patch(
            "llama_cpp.llama_chat_format.Llava15ChatHandler"
        ) as mock_handler, patch(
            "triage_sandbox.Llama"
        ) as mock_llama, patch(
            "triage_sandbox.cleanup_after_run"
        ) as mock_cleanup:
            outcome = triage_sandbox.run_triage(description="duplicate cpu-only offload-unavailable check")

        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["state_hash"], "duplicate-offload-unavailable-hash")
        mock_handler.assert_not_called()
        mock_llama.assert_not_called()
        mock_cleanup.assert_called_once()

    def test_run_triage_skips_model_load_for_duplicate_reduced_gpu_layers_blocked_state(self):
        self._write_gold_set()
        self._write_file("data/images/sample.jpg", "image-bytes")

        def blocked_reason_match(_state_hash, fragment):
            return fragment == "runtime reduced gpu layers"

        with patch(
            "triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")
        ), patch(
            "triage_sandbox.compute_state_hash", return_value="duplicate-reduced-layers-hash"
        ), patch("triage_sandbox.load_recorded_state_hashes", return_value=set()), patch(
            "triage_sandbox.llama_cpp.llama_supports_gpu_offload", return_value=True
        ), patch(
            "triage_sandbox.torch.cuda.is_available", return_value=True
        ), patch(
            "triage_sandbox.detect_free_vram_mb", return_value=4000
        ), patch(
            "triage_sandbox.has_blocked_reason_for_state_hash", side_effect=blocked_reason_match
        ), patch(
            "llama_cpp.llama_chat_format.Llava15ChatHandler"
        ) as mock_handler, patch(
            "triage_sandbox.Llama"
        ) as mock_llama, patch(
            "triage_sandbox.cleanup_after_run"
        ) as mock_cleanup:
            outcome = triage_sandbox.run_triage(description="duplicate reduced-gpu-layer blocked check")

        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["state_hash"], "duplicate-reduced-layers-hash")
        mock_handler.assert_not_called()
        mock_llama.assert_not_called()
        mock_cleanup.assert_called_once()

    def test_run_triage_skips_model_load_for_duplicate_guarded_cpu_capped_diagnostic_blocked_state(self):
        self._write_gold_set()
        self._write_file("data/images/sample.jpg", "image-bytes")

        def blocked_reason_match(_state_hash, fragment):
            return fragment == "guarded cpu fallback used capped sample diagnostic run"

        with patch.object(triage_sandbox, "TRIAGE_ALLOW_GUARDED_CPU_BENCHMARK", True), patch.object(
            triage_sandbox, "TRIAGE_CPU_GUARD_MAX_SAMPLES", 4
        ), patch.object(
            triage_sandbox, "EVAL_MAX_SAMPLES", 0
        ), patch(
            "triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")
        ), patch(
            "triage_sandbox.compute_state_hash", return_value="duplicate-guarded-cpu-cap-hash"
        ), patch("triage_sandbox.load_recorded_state_hashes", return_value=set()), patch(
            "triage_sandbox.torch.cuda.is_available", return_value=False
        ), patch(
            "triage_sandbox.has_blocked_reason_for_state_hash", side_effect=blocked_reason_match
        ), patch(
            "llama_cpp.llama_chat_format.Llava15ChatHandler"
        ) as mock_handler, patch(
            "triage_sandbox.Llama"
        ) as mock_llama, patch(
            "triage_sandbox.cleanup_after_run"
        ) as mock_cleanup:
            outcome = triage_sandbox.run_triage(
                description="duplicate guarded-cpu capped-diagnostic blocked pre-load check"
            )

        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["state_hash"], "duplicate-guarded-cpu-cap-hash")
        mock_handler.assert_not_called()
        mock_llama.assert_not_called()
        mock_cleanup.assert_called_once()

    def test_run_triage_skips_model_load_for_duplicate_runtime_low_vram_cpu_fallback_blocked_state(self):
        self._write_gold_set()
        self._write_file("data/images/sample.jpg", "image-bytes")

        def blocked_reason_match(_state_hash, fragment):
            return fragment == "runtime low-vram cpu fallback active"

        with patch.object(triage_sandbox, "TRIAGE_ALLOW_GUARDED_CPU_BENCHMARK", False), patch(
            "triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")
        ), patch(
            "triage_sandbox.compute_state_hash", return_value="duplicate-runtime-low-vram-cpu-fallback-hash"
        ), patch("triage_sandbox.load_recorded_state_hashes", return_value=set()), patch(
            "triage_sandbox.llama_cpp.llama_supports_gpu_offload", return_value=True
        ), patch(
            "triage_sandbox.torch.cuda.is_available", return_value=True
        ), patch(
            "triage_sandbox.detect_free_vram_mb", return_value=512
        ), patch(
            "triage_sandbox.has_blocked_reason_for_state_hash", side_effect=blocked_reason_match
        ), patch(
            "llama_cpp.llama_chat_format.Llava15ChatHandler"
        ) as mock_handler, patch(
            "triage_sandbox.Llama"
        ) as mock_llama, patch(
            "triage_sandbox.cleanup_after_run"
        ) as mock_cleanup:
            outcome = triage_sandbox.run_triage(
                description="duplicate runtime low-vram cpu fallback blocked pre-load check"
            )

        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["state_hash"], "duplicate-runtime-low-vram-cpu-fallback-hash")
        mock_handler.assert_not_called()
        mock_llama.assert_not_called()
        mock_cleanup.assert_called_once()

    def test_run_triage_skips_model_load_for_duplicate_latency_outlier_blocked_state(self):
        self._write_gold_set()
        self._write_file("data/images/sample.jpg", "image-bytes")

        def blocked_reason_match(_state_hash, fragment):
            return fragment == "latency outlier vs same-state median"

        with patch(
            "triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")
        ), patch(
            "triage_sandbox.compute_state_hash", return_value="duplicate-latency-outlier-hash"
        ), patch("triage_sandbox.load_recorded_state_hashes", return_value=set()), patch(
            "triage_sandbox.has_blocked_reason_for_state_hash", side_effect=blocked_reason_match
        ), patch(
            "llama_cpp.llama_chat_format.Llava15ChatHandler"
        ) as mock_handler, patch(
            "triage_sandbox.Llama"
        ) as mock_llama, patch(
            "triage_sandbox.cleanup_after_run"
        ) as mock_cleanup:
            outcome = triage_sandbox.run_triage(
                description="duplicate latency-outlier blocked pre-load check"
            )

        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["state_hash"], "duplicate-latency-outlier-hash")
        mock_handler.assert_not_called()
        mock_llama.assert_not_called()
        mock_cleanup.assert_called_once()

    def test_run_triage_records_latency_outlier_block_then_short_circuits_duplicate_rerun(self):
        self._write_gold_set()
        self._write_file("data/images/sample.jpg", "image-bytes")

        llm = MagicMock()
        llm.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "[infrastructure_and_utility_damage]"}}]
        }

        def fake_eval(triage_fn, max_samples=None):
            triage_fn("N/A", image_path="data/images/sample.jpg")
            return {"accuracy": 0.90, "f1": 0.88, "total": 1}

        with patch(
            "triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")
        ), patch(
            "triage_sandbox.compute_state_hash", return_value="latency-outlier-lifecycle-hash"
        ), patch("triage_sandbox.load_recorded_state_hashes", return_value=set()), patch(
            "llama_cpp.llama_chat_format.Llava15ChatHandler", return_value=MagicMock()
        ), patch(
            "triage_sandbox.detect_free_vram_mb", return_value=5000
        ), patch(
            "triage_sandbox.llama_cpp.llama_supports_gpu_offload", return_value=True
        ), patch(
            "triage_sandbox.Llama", return_value=llm
        ), patch(
            "triage_sandbox.evaluate_triage", side_effect=fake_eval
        ), patch(
            "triage_sandbox.load_best_recorded_f1", return_value=0.95
        ), patch(
            "triage_sandbox.detect_latency_outlier_for_state_hash",
            return_value={
                "median_latency_ms": 160.0,
                "outlier_threshold_ms": 232.0,
                "history_count": 3,
            },
        ), patch(
            "triage_sandbox.has_blocked_reason_for_state_hash", return_value=False
        ), patch(
            "triage_sandbox.cleanup_after_run"
        ), patch(
            "triage_sandbox.detect_process_vram_mb", return_value=256.0
        ), patch(
            "triage_sandbox.torch.cuda.is_available", return_value=False
        ):
            first_outcome = triage_sandbox.run_triage(description="latency outlier lifecycle first pass")

        self.assertEqual(first_outcome["status"], "blocked")
        first_rows = Path("results.tsv").read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(first_rows), 2)
        self.assertIn("blocked: latency outlier vs same-state median", first_rows[-1])

        def blocked_reason_match(_state_hash, fragment):
            return fragment == "latency outlier vs same-state median"

        with patch(
            "triage_sandbox.preflight_data_health", return_value=(True, "ready", "inputs ready")
        ), patch(
            "triage_sandbox.compute_state_hash", return_value="latency-outlier-lifecycle-hash"
        ), patch("triage_sandbox.load_recorded_state_hashes", return_value=set()), patch(
            "triage_sandbox.has_blocked_reason_for_state_hash", side_effect=blocked_reason_match
        ), patch(
            "llama_cpp.llama_chat_format.Llava15ChatHandler"
        ) as mock_handler, patch(
            "triage_sandbox.Llama"
        ) as mock_llama, patch(
            "triage_sandbox.cleanup_after_run"
        ) as mock_cleanup:
            second_outcome = triage_sandbox.run_triage(
                description="latency outlier lifecycle duplicate pass"
            )

        self.assertEqual(second_outcome["status"], "blocked")
        self.assertEqual(second_outcome["state_hash"], "latency-outlier-lifecycle-hash")
        mock_handler.assert_not_called()
        mock_llama.assert_not_called()
        mock_cleanup.assert_called_once()
        second_rows = Path("results.tsv").read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(second_rows), 2)


if __name__ == "__main__":
    unittest.main()
