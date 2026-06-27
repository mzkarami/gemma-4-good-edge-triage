import argparse
import os

from rich.console import Console
from rich.panel import Panel

from edge_triage_core.config import TriageRuntimeConfig
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

    result = output["choices"][0]["message"]["content"]
    console.print(Panel(result, title="[bold cyan]Triage Report & Advice[/bold cyan]"))


if __name__ == "__main__":
    main()
