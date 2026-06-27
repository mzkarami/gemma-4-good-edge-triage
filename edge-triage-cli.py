import argparse
import json
import os
from datetime import datetime, timezone

from rich.console import Console
from rich.panel import Panel

from edge_triage_core.config import TriageRuntimeConfig
from edge_triage_core.labels import parse_label
from edge_triage_core.results import build_triage_response
from edge_triage_core.prompts import TRIAGE_SYSTEM_PROMPT, resolve_main_prompt_template
from litert_backend import NativeAudioProcessor

console = Console()


def get_latest_field_prompt():
    return resolve_main_prompt_template()


def load_llama_runtime():
    """Load native llama.cpp bindings only when a real triage run needs them."""
    from llama_cpp import Llama
    from llama_cpp.llama_chat_format import Llava15ChatHandler

    return Llama, Llava15ChatHandler


def main():
    parser = argparse.ArgumentParser(description="Edge-Triage Field Tool")
    parser.add_argument("--image", help="Path to disaster photo")
    parser.add_argument("--report", help="Text description of the scene")
    parser.add_argument("--audio", help="Path to audio file (hands-free triage)")
    parser.add_argument("--save-case", help="Append triage result to a local JSONL incident queue")
    parser.add_argument("--language", default="en", choices=["en", "es"], help="Output language for radio script")
    parser.add_argument("--format", default="standard", choices=["standard", "radio"], help="Output format hint")
    args = parser.parse_args()

    if not args.image and not args.report and not args.audio:
        parser.print_help()
        return

    Llama, Llava15ChatHandler = load_llama_runtime()

    config = TriageRuntimeConfig.local_from_env()

    console.print(Panel("[bold green]Starting Edge-Triage Field Tool...[/bold green]\nReady for offline disaster response."))

    # 0. Handle Audio (LiteRT Ears)
    scenario = args.report or "No text report provided."
    if args.audio:
        console.print("👂 [bold yellow]Processing Audio with Native LiteRT Processor...[/bold yellow]")
        ears = NativeAudioProcessor()
        transcript = ears.transcribe(args.audio)
        console.print(f"✅ Transcript: [italic]{transcript}[/italic]")
        # Combine speech with any manual report
        scenario = f"{scenario} (Voice Report: {transcript})"

    # Load model (optimized for field)
    console.print(f"Loading model from {config.model_path}...")
    chat_handler = Llava15ChatHandler(clip_model_path=str(config.mmproj_path), verbose=False)
    llm = Llama(
        model_path=str(config.model_path),
        chat_handler=chat_handler,
        n_ctx=config.n_ctx,
        n_gpu_layers=config.n_gpu_layers,
        verbose=False,
    )

    # Run Triage
    image_content = []
    if args.image and os.path.exists(args.image):
        abs_path = os.path.abspath(args.image)
        image_content = [{"type": "image_url", "image_url": f"file://{abs_path}"}]

    console.print("Processing triage...")
    output = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": get_latest_field_prompt().replace("{scenario}", scenario)},
                    *image_content,
                ],
            },
        ],
        max_tokens=300,  # Increased for advice
        temperature=0.1,
    )

    result = str(output["choices"][0]["message"].get("content") or "")
    label = parse_label(result)
    response = build_triage_response(
        label,
        0.0,
        True,
        result,
        note=scenario,
        filename=args.image or args.audio,
        language=args.language,
        output_format=args.format,
    )
    if args.format == "radio":
        result_text = response["radio_script"]
    else:
        result_text = (
            f"Label: {response['label']}\n"
            f"Priority: {response['priority']}\n"
            f"Safe next action: {response['next_action']}\n"
            f"Do not do: {response['action_pack']['do_not_do']}\n"
            f"Collect next: {', '.join(response['action_pack']['collect_next'])}\n"
            f"Escalate if: {', '.join(response['action_pack']['escalate_if'])}\n"
            f"Radio script: {response['radio_script']}"
        )
    console.print(Panel(result_text, title="[bold cyan]Triage Report & Advice[/bold cyan]"))
    if args.save_case:
        record = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "report": scenario,
            "image": args.image,
            "audio": args.audio,
            "triage": response,
            "synced": False,
        }
        with open(args.save_case, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        console.print(f"Saved local incident queue entry to {args.save_case}")


if __name__ == "__main__":
    main()
