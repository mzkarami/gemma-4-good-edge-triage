import asyncio
import hmac
import json
import os
import re
import tempfile
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Deque, NoReturn, cast

from fastapi import FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageOps, UnidentifiedImageError

from edge_triage_core.config import TriageRuntimeConfig
from edge_triage_core.labels import (
    fallback_classify,
    fallback_scene_summary,
    parse_label,
    sanitize_model_text,
    sanitize_note as _sanitize_note,
)
from edge_triage_core.prompts import LIVE_API_PROMPT_TEMPLATE, LIVE_API_SYSTEM_PROMPT
from edge_triage_core.results import build_triage_response

MAX_UPLOAD_BYTES = int(os.getenv("EDGE_TRIAGE_MAX_UPLOAD_MB", "25")) * 1024 * 1024
MAX_NOTE_CHARS = int(os.getenv("EDGE_TRIAGE_MAX_NOTE_CHARS", "1000"))
MAX_IMAGE_PIXELS = int(os.getenv("EDGE_TRIAGE_MAX_IMAGE_PIXELS", "36000000"))
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
TEMP_ROOT = os.getenv("EDGE_TRIAGE_TEMP_ROOT") or "/tmp"
MODEL_LOCK = asyncio.Lock()
RATE_LIMIT_PER_MINUTE = int(os.getenv("EDGE_TRIAGE_RATE_LIMIT_PER_MINUTE", "6"))
RATE_LIMIT_PER_DAY = int(os.getenv("EDGE_TRIAGE_RATE_LIMIT_PER_DAY", "60"))
PUBLIC_API_ENABLED = os.getenv("EDGE_TRIAGE_PUBLIC_API_ENABLED", "1") != "0"
MAX_CONCURRENT_REQUESTS = int(os.getenv("EDGE_TRIAGE_MAX_CONCURRENT_REQUESTS", "2"))
RATE_BUCKETS: dict[str, Deque[float]] = defaultdict(deque)
DAY_BUCKETS: dict[str, Deque[float]] = defaultdict(deque)
INFLIGHT_LOCK = asyncio.Lock()
INFLIGHT_REQUESTS = 0
LIVE_MODEL = os.getenv("EDGE_TRIAGE_LIVE_MODEL", "0") == "1"
RUNTIME_CONFIG = TriageRuntimeConfig.live_api_from_env()
MODEL_PATH = str(RUNTIME_CONFIG.model_path)
MMPROJ_PATH = str(RUNTIME_CONFIG.mmproj_path)
N_CTX = RUNTIME_CONFIG.n_ctx
N_GPU_LAYERS = RUNTIME_CONFIG.n_gpu_layers
GEN_TEMPERATURE = RUNTIME_CONFIG.temperature
TRIAGE_SYSTEM_PROMPT = LIVE_API_SYSTEM_PROMPT
TRIAGE_PROMPT_TEMPLATE = LIVE_API_PROMPT_TEMPLATE

Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

app = FastAPI(title="Edge-Triage Live API", version="0.1.0")

_allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "EDGE_TRIAGE_ALLOWED_ORIGINS",
        "http://localhost:4173,http://127.0.0.1:4173",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "X-Judge-Token", "Content-Type"],
    max_age=300,
)

def _error(status_code: int, detail: str) -> NoReturn:
    raise HTTPException(status_code=status_code, detail=detail)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.get("/healthz")
def healthz():
    return {"ok": True}


def _configured_token() -> str:
    token = os.getenv("EDGE_TRIAGE_JUDGE_TOKEN", "").strip()
    if not token:
        _error(503, "Live inference is not configured yet.")
    return token


def _extract_token(authorization: str | None, x_judge_token: str | None) -> str | None:
    if x_judge_token:
        return x_judge_token.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def _require_token(authorization: str | None, x_judge_token: str | None) -> str:
    supplied = _extract_token(authorization, x_judge_token)
    if not supplied:
        _error(401, "Judge token required. Use the token from the Kaggle submission notes.")
    expected = _configured_token()
    if not hmac.compare_digest(supplied, expected):
        _error(403, "Invalid judge token.")
    return supplied


def _client_key(request: Request, token: str | None = None) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    ip = forwarded or (request.client.host if request.client else "unknown")
    suffix = token[:8] if token else "public"
    return f"{ip}:{suffix}"


def _check_rate_limit(key: str, now: float | None = None):
    now = now or time.time()
    minute_bucket = RATE_BUCKETS[key]
    while minute_bucket and now - minute_bucket[0] > 60:
        minute_bucket.popleft()
    if len(minute_bucket) >= RATE_LIMIT_PER_MINUTE:
        _error(429, "Rate limit reached. Please wait a minute and try again. The curated offline demo is still available.")
    minute_bucket.append(now)

    day_bucket = DAY_BUCKETS[key]
    while day_bucket and now - day_bucket[0] > 86400:
        day_bucket.popleft()
    if len(day_bucket) >= RATE_LIMIT_PER_DAY:
        _error(429, "Daily Live Gemma preview limit reached. The curated offline demo is still available.")
    day_bucket.append(now)


async def _enter_public_request() -> None:
    global INFLIGHT_REQUESTS
    if not PUBLIC_API_ENABLED:
        _error(503, "Live analysis is temporarily disabled; the curated offline demo is still available.")
    async with INFLIGHT_LOCK:
        if INFLIGHT_REQUESTS >= MAX_CONCURRENT_REQUESTS:
            _error(429, "Live analysis is busy; please try again shortly. The curated offline demo is still available.")
        INFLIGHT_REQUESTS += 1


async def _leave_public_request() -> None:
    global INFLIGHT_REQUESTS
    async with INFLIGHT_LOCK:
        INFLIGHT_REQUESTS = max(0, INFLIGHT_REQUESTS - 1)


def sanitize_note(note: str | None) -> str:
    return _sanitize_note(note, max_chars=MAX_NOTE_CHARS)


async def read_limited_upload(upload: UploadFile) -> bytes:
    if upload.content_type not in ALLOWED_CONTENT_TYPES:
        _error(415, "Unsupported image type. Use JPEG, PNG, or WebP.")
    chunks = []
    total = 0
    while True:
        chunk = await upload.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_UPLOAD_BYTES:
            _error(413, "Image must be 25 MB or smaller.")
        chunks.append(chunk)
    if total == 0:
        _error(400, "Image upload is empty.")
    return b"".join(chunks)


def sanitize_image(upload_bytes: bytes, directory: str) -> str:
    try:
        from io import BytesIO

        with Image.open(BytesIO(upload_bytes)) as image:
            image.verify()
        with Image.open(BytesIO(upload_bytes)) as image:
            image = ImageOps.exif_transpose(image)
            image.load()
            if image.width * image.height > MAX_IMAGE_PIXELS:
                _error(413, "Image dimensions are too large for the Live Gemma preview.")
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            path = Path(directory) / "upload_sanitized.jpg"
            image.save(path, format="JPEG", quality=88, optimize=True)
            return str(path)
    except (UnidentifiedImageError, OSError, SyntaxError):
        _error(415, "Uploaded file is not a valid image.")
    except Image.DecompressionBombError:
        _error(413, "Image dimensions are too large for the Live Gemma preview.")
    _error(415, "Uploaded file is not a valid image.")


def parse_live_output(raw_text: str) -> tuple[str, str]:
    raw_text = raw_text.strip()
    match = re.search(r"\{.*\}", raw_text, flags=re.S)
    if match:
        try:
            parsed = json.loads(match.group(0))
            label = parse_label(str(parsed.get("label", "")))
            summary = sanitize_model_text(parsed.get("scene_summary"))
            if summary:
                return label, summary
        except (json.JSONDecodeError, TypeError):
            pass
    label = parse_label(raw_text)
    return label, "Gemma returned a label but no safe bounded scene summary."


def run_live_model(image_path: str, note: str) -> tuple[str, str]:
    from llama_cpp import Llama
    from llama_cpp.llama_chat_format import Llava15ChatHandler

    if not Path(MODEL_PATH).exists() or not Path(MMPROJ_PATH).exists():
        _error(503, "Live model files are not mounted; the curated offline demo is still available.")

    chat_handler = Llava15ChatHandler(clip_model_path=MMPROJ_PATH, verbose=False)
    llm = Llama(
        model_path=MODEL_PATH,
        chat_handler=chat_handler,
        n_ctx=N_CTX,
        n_gpu_layers=N_GPU_LAYERS,
        verbose=False,
    )
    output = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": TRIAGE_PROMPT_TEMPLATE.replace("{scenario}", note or "No text report provided.")},
                    {"type": "image_url", "image_url": f"file://{os.path.abspath(image_path)}"},
                ],
            },
        ],
        max_tokens=80,
        temperature=GEN_TEMPERATURE,
    )
    response = cast(dict, output)
    raw = str(response["choices"][0]["message"].get("content") or "")
    return parse_live_output(raw)


@app.post("/api/triage")
async def triage(
    request: Request,
    image: UploadFile = File(...),
    note: str = Form(""),
    authorization: str | None = Header(default=None),
    x_judge_token: str | None = Header(default=None),
):
    token = _extract_token(authorization, x_judge_token)
    await _enter_public_request()
    try:
        _check_rate_limit(_client_key(request, token))
        started = time.perf_counter()
        safe_note = sanitize_note(note)
        upload_bytes = await read_limited_upload(image)

        try:
            with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp_dir:
                sanitized_path = sanitize_image(upload_bytes, temp_dir)
                async with MODEL_LOCK:
                    if LIVE_MODEL:
                        try:
                            label, scene_summary = await asyncio.wait_for(
                                asyncio.to_thread(run_live_model, sanitized_path, safe_note),
                                timeout=float(os.getenv("EDGE_TRIAGE_MODEL_TIMEOUT_SECONDS", "30")),
                            )
                            live = True
                        except Exception:
                            _error(503, "Live model unavailable; the curated offline demo is still available.")
                    else:
                        label = fallback_classify(safe_note, image.filename)
                        scene_summary = fallback_scene_summary(label, safe_note, image.filename)
                        live = False
        finally:
            await image.close()

        latency_ms = (time.perf_counter() - started) * 1000
        return build_triage_response(label, latency_ms, live, scene_summary, note=safe_note, filename=image.filename)
    finally:
        await _leave_public_request()
