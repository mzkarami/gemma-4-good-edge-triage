import unittest
import sys
import os

# Ensure we can import from the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import triage_sandbox
import importlib.util
from unittest.mock import MagicMock, patch

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

def import_field_tool():
    spec = importlib.util.spec_from_file_location("edge_triage_cli", "edge-triage-cli.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

edge_triage_cli = import_field_tool()

class TestFieldTool(unittest.TestCase):
    def test_imports_active_prompt(self):
        prompt = edge_triage_cli.get_latest_field_prompt()
        self.assertEqual(prompt, triage_sandbox.TRIAGE_PROMPT_TEMPLATE)

    def test_audio_transcript_is_preserved_in_prompt(self):
        llm = MagicMock()
        llm.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "[infrastructure_and_utility_damage]"}}]
        }
        ears = MagicMock()
        ears.transcribe.return_value = "bridge damage reported by voice"

        with patch.object(sys, "argv", [
            "edge-triage-cli.py",
            "--report",
            "manual flood report",
            "--audio",
            "report.wav",
        ]), patch.object(edge_triage_cli, "NativeAudioProcessor", return_value=ears), patch.object(
            edge_triage_cli, "Llava15ChatHandler", return_value=MagicMock()
        ), patch.object(edge_triage_cli, "Llama", return_value=llm):
            edge_triage_cli.main()

        prompt_text = llm.create_chat_completion.call_args.kwargs["messages"][1]["content"][0]["text"]
        self.assertIn("manual flood report", prompt_text)
        self.assertIn("bridge damage reported by voice", prompt_text)

if __name__ == "__main__":
    unittest.main()
