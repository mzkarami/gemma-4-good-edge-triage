import builtins
import importlib
import os
import unittest
from unittest.mock import patch


class EdgeTriageCoreTest(unittest.TestCase):
    def test_core_import_has_no_heavy_side_effect_imports(self):
        blocked = {"triage_sandbox", "llama_cpp", "torch", "prepare", "local_extractor"}
        real_import = builtins.__import__

        def guarded_import(name, *args, **kwargs):
            root = name.split(".")[0]
            if root in blocked:
                raise AssertionError(f"edge_triage_core imported heavy module {name}")
            return real_import(name, *args, **kwargs)

        with patch.object(builtins, "__import__", side_effect=guarded_import):
            import edge_triage_core
            importlib.reload(edge_triage_core)

    def test_prompt_variant_resolution(self):
        from edge_triage_core.prompts import resolve_main_prompt_template

        baseline = resolve_main_prompt_template("baseline")
        guarded = resolve_main_prompt_template("severe_dt0_rescue_guard")
        strict = resolve_main_prompt_template("severe_dt0_rescue_guard_strict")

        self.assertIn("Report: {scenario}", baseline)
        self.assertIn("do not choose rescue unless active aid", guarded)
        self.assertIn("Rescue requires at least one direct aid cue", strict)

    def test_label_helpers_match_public_fallback_contract(self):
        from edge_triage_core.labels import fallback_classify, fallback_scene_summary, parse_label

        self.assertEqual(fallback_classify("bridge washed out", "bridge.png"), "infrastructure_and_utility_damage")
        self.assertEqual(fallback_classify("firefighter extinguishing forest fire", "fire.jpg"), "rescue_volunteering_or_donation_effort")
        self.assertEqual(parse_label("[affected_injured_or_dead_people] likely casualty"), "affected_injured_or_dead_people")
        summary = fallback_scene_summary("infrastructure_and_utility_damage", "bridge token: secret123", "bridge.png")
        self.assertIn("Guarded fallback", summary)
        self.assertNotIn("secret123", summary)

    def test_runtime_config_defaults_are_side_effect_free(self):
        from edge_triage_core.config import TriageRuntimeConfig

        with patch.dict(os.environ, {}, clear=True):
            config = TriageRuntimeConfig.local_from_env()

        self.assertEqual(config.n_ctx, 933)
        self.assertEqual(config.n_gpu_layers, 47)
        self.assertTrue(config.model_path.name.startswith("Edge-Triage-"))

    def test_response_builder_shape(self):
        from edge_triage_core.results import build_triage_response

        body = build_triage_response("not_humanitarian", 12.345, False, "token: abc123 visible")
        self.assertEqual(body["label"], "not_humanitarian")
        self.assertEqual(body["latency_ms"], 12.35)
        self.assertFalse(body["live_model"])
        self.assertNotIn("abc123", body["scene_summary"])
        self.assertIn("decision support", body["disclaimer"].lower())
        self.assertIn("action_pack", body)
        self.assertIn("radio_script", body)
        self.assertIn("guidance_basis", body)
        self.assertTrue(body["guidance_basis"])
        self.assertTrue(any("review" in item.lower() or "route" in item.lower() or "keep" in item.lower() for item in body["guidance_basis"]))

    def test_red_flag_override_forces_human_safety_escalation(self):
        from edge_triage_core.results import build_triage_response

        body = build_triage_response(
            "infrastructure_and_utility_damage",
            10,
            False,
            "bridge report",
            note="collapsed bridge with trapped person and live wires",
        )
        self.assertEqual(body["label"], "affected_injured_or_dead_people")
        self.assertTrue(body["red_flag_escalation"])
        self.assertGreaterEqual(len(body["red_flags"]), 1)
        self.assertIn("trained medical/rescue", body["next_action"])
        self.assertTrue(any("red-flag" in item.lower() for item in body["guidance_basis"]))

    def test_spanish_radio_script_is_available(self):
        from edge_triage_core.results import build_triage_response

        body = build_triage_response("infrastructure_and_utility_damage", 10, False, "bridge", language="es", output_format="radio")
        self.assertEqual(body["language"], "es")
        self.assertEqual(body["output_format"], "radio")
        self.assertIn("Reporte de campo", body["radio_script"])


if __name__ == "__main__":
    unittest.main()
