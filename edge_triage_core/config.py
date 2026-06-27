"""Runtime configuration shared by Edge-Triage product surfaces."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CACHE_DIR = Path.home() / ".cache" / "autoresearch"
DEFAULT_MODEL_DIR = DEFAULT_CACHE_DIR / "models"
DEFAULT_MODEL_FILENAME = "gemma-4-E4B-it-Q3_K_M.gguf"
DEFAULT_EDGE_MODEL_FILENAME = f"Edge-Triage-{DEFAULT_MODEL_FILENAME}"
DEFAULT_MMPROJ_FILENAME = "Edge-Triage-mmproj-F16.gguf"
DEFAULT_ALT_MMPROJ_FILENAME = "mmproj-F16.gguf"
DEFAULT_CONTAINER_MODEL_PATH = Path("/app/models") / DEFAULT_EDGE_MODEL_FILENAME
DEFAULT_CONTAINER_MMPROJ_PATH = Path("/app/models") / DEFAULT_MMPROJ_FILENAME


@dataclass(frozen=True)
class TriageRuntimeConfig:
    model_dir: Path
    model_filename: str
    model_path: Path
    mmproj_path: Path
    alt_mmproj_path: Path
    n_ctx: int
    n_gpu_layers: int
    temperature: float

    @classmethod
    def local_from_env(cls) -> "TriageRuntimeConfig":
        model_dir = Path(os.getenv("EDGE_TRIAGE_MODEL_DIR", str(DEFAULT_MODEL_DIR))).expanduser()
        model_filename = os.getenv("EDGE_TRIAGE_MODEL_FILENAME", DEFAULT_MODEL_FILENAME)
        edge_model_filename = (
            model_filename if model_filename.startswith("Edge-Triage-") else f"Edge-Triage-{model_filename}"
        )
        model_path = Path(os.getenv("EDGE_TRIAGE_MODEL_PATH", str(model_dir / edge_model_filename))).expanduser()
        alt_mmproj_path = Path(os.getenv("EDGE_TRIAGE_ALT_MMPROJ_PATH", str(model_dir / DEFAULT_ALT_MMPROJ_FILENAME))).expanduser()
        configured_mmproj = Path(
            os.getenv("EDGE_TRIAGE_MMPROJ_PATH", str(model_dir / DEFAULT_MMPROJ_FILENAME))
        ).expanduser()
        mmproj_path = alt_mmproj_path if not configured_mmproj.exists() and alt_mmproj_path.exists() else configured_mmproj
        return cls(
            model_dir=model_dir,
            model_filename=model_filename,
            model_path=model_path,
            mmproj_path=mmproj_path,
            alt_mmproj_path=alt_mmproj_path,
            n_ctx=int(os.getenv("TRIAGE_N_CTX", "933")),
            n_gpu_layers=int(os.getenv("TRIAGE_N_GPU_LAYERS", "47")),
            temperature=float(os.getenv("TRIAGE_GEN_TEMPERATURE", "0.0")),
        )

    @classmethod
    def live_api_from_env(cls) -> "TriageRuntimeConfig":
        model_path = Path(os.getenv("EDGE_TRIAGE_MODEL_PATH", str(DEFAULT_CONTAINER_MODEL_PATH)))
        mmproj_path = Path(os.getenv("EDGE_TRIAGE_MMPROJ_PATH", str(DEFAULT_CONTAINER_MMPROJ_PATH)))
        return cls(
            model_dir=model_path.parent,
            model_filename=model_path.name.removeprefix("Edge-Triage-"),
            model_path=model_path,
            mmproj_path=mmproj_path,
            alt_mmproj_path=model_path.parent / DEFAULT_ALT_MMPROJ_FILENAME,
            n_ctx=int(os.getenv("TRIAGE_N_CTX", "933")),
            n_gpu_layers=int(os.getenv("TRIAGE_N_GPU_LAYERS", "47")),
            temperature=float(os.getenv("TRIAGE_GEN_TEMPERATURE", "0.0")),
        )
