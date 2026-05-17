import argparse
import os
import sys
from rich.console import Console
from rich.panel import Panel
# We want to import from triage_sandbox to keep the prompt synced
from triage_sandbox import TRIAGE_PROMPT_TEMPLATE, TRIAGE_SYSTEM_PROMPT, MODEL_PATH, MMPROJ_PATH, N_CTX, N_GPU_LAYERS
from llama_cpp import Llama
from llama_cpp.llama_chat_format import Llava15ChatHandler

from litert_backend import NativeAudioProcessor

console = Console()

def get_latest_field_prompt():
    return TRIAGE_PROMPT_TEMPLATE

def main():
    parser = argparse.ArgumentParser(description="Edge-Triage Field Tool")
    parser.add_argument("--image", help="Path to disaster photo")
    parser.add_argument("--report", help="Text description of the scene")
    parser.add_argument("--audio", help="Path to audio file (hands-free triage)")
    args = parser.parse_args()
    
    if not args.image and not args.report and not args.audio:
        parser.print_help()
        return

    console.print(Panel("[bold green]Starting Edge-Triage Field Tool...[/bold green]\nReady for offline disaster response."))
    
    # 0. Handle Audio (LiteRT Ears)
    scenario = args.report or "No text report provided."
    if args.audio:
        console.print(f"👂 [bold yellow]Processing Audio with Native LiteRT Processor...[/bold yellow]")
        ears = NativeAudioProcessor()
        transcript = ears.transcribe(args.audio)
        console.print(f"✅ Transcript: [italic]{transcript}[/italic]")
        # Combine speech with any manual report
        scenario = f"{scenario} (Voice Report: {transcript})"

    # Load model (optimized for field)
    console.print(f"Loading model from {MODEL_PATH}...")
    chat_handler = Llava15ChatHandler(clip_model_path=MMPROJ_PATH, verbose=False)
    llm = Llama(
        model_path=MODEL_PATH,
        chat_handler=chat_handler,
        n_ctx=N_CTX,
        n_gpu_layers=N_GPU_LAYERS,
        verbose=False
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
                    {"type": "text", "text": TRIAGE_PROMPT_TEMPLATE.replace("{scenario}", scenario)},
                    *image_content
                ]
            }
        ],
        max_tokens=300, # Increased for advice
        temperature=0.1,
    )
    
    result = output["choices"][0]["message"]["content"]
    console.print(Panel(result, title="[bold cyan]Triage Report & Advice[/bold cyan]"))

if __name__ == "__main__":
    main()
