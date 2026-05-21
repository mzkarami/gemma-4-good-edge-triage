"""
One-time data preparation for autoresearch experiments.
Downloads data shards, trains a BPE tokenizer, and prepares model artifacts.

Sources are checked in this order where applicable:
1. attached Kaggle notebook inputs under /kaggle/input,
2. existing local cache under ~/.cache/autoresearch/,
3. optional Kaggle dataset slugs from EDGE_TRIAGE_KAGGLE_MODEL_DATASET / EDGE_TRIAGE_KAGGLE_DATASET,
4. Hugging Face fallback.

Usage:
    python prepare.py                  # full prep (download + tokenizer)
    python prepare.py --num-shards 8   # download only 8 shards (for testing)

Data and tokenizer are stored in ~/.cache/autoresearch/.
"""

import os
import sys
import time
import math
import argparse
import pickle
import json
import subprocess
import shutil
from multiprocessing import Pool

import requests
import pyarrow.parquet as pq
import rustbpe
import tiktoken
import torch
from huggingface_hub import hf_hub_download
from sklearn.metrics import f1_score, accuracy_score

# ---------------------------------------------------------------------------
# Constants (fixed, do not modify)
# ---------------------------------------------------------------------------

MAX_SEQ_LEN = 2048       # context length
TIME_BUDGET = 300        # training time budget in seconds (5 minutes)
EVAL_TOKENS = 40 * 524288  # number of tokens for val eval

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "autoresearch")
DATA_DIR = os.path.join(CACHE_DIR, "data")
TOKENIZER_DIR = os.path.join(CACHE_DIR, "tokenizer")
TRIAGE_DATA_DIR = os.path.join(CACHE_DIR, "triage_data")
MODEL_DIR = os.path.join(CACHE_DIR, "models")
BASE_URL = "https://huggingface.co/datasets/karpathy/climbmix-400b-shuffle/resolve/main"
MAX_SHARD = 6542 # the last datashard is shard_06542.parquet
VAL_SHARD = MAX_SHARD  # pinned validation shard (shard_06542)
VAL_FILENAME = f"shard_{VAL_SHARD:05d}.parquet"
VOCAB_SIZE = 8192

# BPE split pattern (GPT-4 style, with \p{N}{1,2} instead of {1,3})
SPLIT_PATTERN = r"""'(?i:[sdmt]|ll|ve|re)|[^\r\n\p{L}\p{N}]?+\p{L}+|\p{N}{1,2}| ?[^\s\p{L}\p{N}]++[\r\n]*|\s*[\r\n]|\s+(?!\S)|\s+"""

SPECIAL_TOKENS = [f"<|reserved_{i}|>" for i in range(4)]
BOS_TOKEN = "<|reserved_0|>"


def normalize_source(source):
    """Return a validated artifact source mode."""
    source = (source or "auto").strip().lower()
    if source not in {"auto", "huggingface", "kaggle"}:
        raise ValueError("source must be one of: auto, huggingface, kaggle")
    return source


def maybe_stage_kaggle_data_shards(ids):
    """Copy requested shard_*.parquet files from attached Kaggle inputs into DATA_DIR."""
    kaggle_input_dir = os.getenv("KAGGLE_INPUT_DIR", "/kaggle/input")
    if not os.path.isdir(kaggle_input_dir):
        return 0

    os.makedirs(DATA_DIR, exist_ok=True)
    wanted = {f"shard_{i:05d}.parquet" for i in ids}
    staged = 0
    for root, _dirs, files in os.walk(kaggle_input_dir):
        for name in files:
            if name not in wanted:
                continue
            src = os.path.join(root, name)
            dst = os.path.join(DATA_DIR, name)
            if os.path.exists(dst):
                continue
            shutil.copy2(src, dst)
            staged += 1
    if staged:
        print(f"Data: staged {staged} shard(s) from Kaggle inputs at {kaggle_input_dir}")
    return staged


def download_kaggle_dataset(dataset_slug, destination_dir):
    """Download and unzip a Kaggle dataset into destination_dir with the Kaggle CLI."""
    if not dataset_slug:
        return False
    os.makedirs(destination_dir, exist_ok=True)
    print(f"Kaggle: downloading {dataset_slug} into {destination_dir}...")
    try:
        subprocess.run(
            [
                "kaggle",
                "datasets",
                "download",
                "-d",
                dataset_slug,
                "-p",
                destination_dir,
                "--unzip",
            ],
            check=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(f"Kaggle: dataset download failed for {dataset_slug}: {exc}")
        return False

# ---------------------------------------------------------------------------
# Data download
# ---------------------------------------------------------------------------

def download_single_shard(index):
    """Download one parquet shard with retries. Returns True on success."""
    filename = f"shard_{index:05d}.parquet"
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        return True

    url = f"{BASE_URL}/{filename}"
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            temp_path = filepath + ".tmp"
            with open(temp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
            os.rename(temp_path, filepath)
            print(f"  Downloaded {filename}")
            return True
        except (requests.RequestException, IOError) as e:
            print(f"  Attempt {attempt}/{max_attempts} failed for {filename}: {e}")
            for path in [filepath + ".tmp", filepath]:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass
            if attempt < max_attempts:
                time.sleep(2 ** attempt)
    return False


def download_data(num_shards, download_workers=8, source="auto"):
    """Download training shards + pinned validation shard."""
    source = normalize_source(source)
    os.makedirs(DATA_DIR, exist_ok=True)
    num_train = min(num_shards, MAX_SHARD)
    ids = list(range(num_train))
    if VAL_SHARD not in ids:
        ids.append(VAL_SHARD)

    # Count what's already downloaded
    existing = sum(1 for i in ids if os.path.exists(os.path.join(DATA_DIR, f"shard_{i:05d}.parquet")))
    if existing == len(ids):
        print(f"Data: all {len(ids)} shards already downloaded at {DATA_DIR}")
        return

    needed = len(ids) - existing
    print(f"Data: downloading {needed} shards ({existing} already exist)...")

    if source in {"auto", "kaggle"}:
        maybe_stage_kaggle_data_shards(ids)
        kaggle_dataset = os.getenv("EDGE_TRIAGE_KAGGLE_DATASET")
        if kaggle_dataset:
            download_kaggle_dataset(kaggle_dataset, DATA_DIR)
        existing = sum(1 for i in ids if os.path.exists(os.path.join(DATA_DIR, f"shard_{i:05d}.parquet")))
        if existing == len(ids):
            print(f"Data: all {len(ids)} shards ready from Kaggle at {DATA_DIR}")
            return
        if source == "kaggle":
            raise RuntimeError(
                "Kaggle source selected but required shards are incomplete. "
                "Attach parquet shards as Kaggle Inputs or set EDGE_TRIAGE_KAGGLE_DATASET=<user/dataset-slug>."
            )
        if kaggle_dataset:
            print(f"Data: Kaggle source provided {existing}/{len(ids)} shards; falling back to Hugging Face for missing shards...")

    workers = max(1, min(download_workers, needed))
    with Pool(processes=workers) as pool:
        results = pool.map(download_single_shard, ids)

    ok = sum(1 for r in results if r)
    print(f"Data: {ok}/{len(ids)} shards ready at {DATA_DIR}")

# ---------------------------------------------------------------------------
# Tokenizer training
# ---------------------------------------------------------------------------

def list_parquet_files():
    """Return sorted list of parquet file paths in the data directory."""
    files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith(".parquet") and not f.endswith(".tmp"))
    return [os.path.join(DATA_DIR, f) for f in files]


def text_iterator(max_chars=1_000_000_000, doc_cap=10_000):
    """Yield documents from training split (all shards except pinned val shard)."""
    parquet_paths = [p for p in list_parquet_files() if not p.endswith(VAL_FILENAME)]
    nchars = 0
    for filepath in parquet_paths:
        pf = pq.ParquetFile(filepath)
        for rg_idx in range(pf.num_row_groups):
            rg = pf.read_row_group(rg_idx)
            for text in rg.column("text").to_pylist():
                doc = text[:doc_cap] if len(text) > doc_cap else text
                nchars += len(doc)
                yield doc
                if nchars >= max_chars:
                    return


def train_tokenizer():
    """Train BPE tokenizer using rustbpe, save as tiktoken pickle."""
    tokenizer_pkl = os.path.join(TOKENIZER_DIR, "tokenizer.pkl")
    token_bytes_path = os.path.join(TOKENIZER_DIR, "token_bytes.pt")

    if os.path.exists(tokenizer_pkl) and os.path.exists(token_bytes_path):
        print(f"Tokenizer: already trained at {TOKENIZER_DIR}")
        return

    os.makedirs(TOKENIZER_DIR, exist_ok=True)

    parquet_files = list_parquet_files()
    if len(parquet_files) < 2:
        print("Tokenizer: need at least 2 data shards (1 train + 1 val). Download more data first.")
        sys.exit(1)

    # --- Train with rustbpe ---
    print("Tokenizer: training BPE tokenizer...")
    t0 = time.time()

    tokenizer = rustbpe.Tokenizer()
    vocab_size_no_special = VOCAB_SIZE - len(SPECIAL_TOKENS)
    tokenizer.train_from_iterator(text_iterator(), vocab_size_no_special, pattern=SPLIT_PATTERN)

    # Build tiktoken encoding from trained merges
    pattern = tokenizer.get_pattern()
    mergeable_ranks = {bytes(k): v for k, v in tokenizer.get_mergeable_ranks()}
    tokens_offset = len(mergeable_ranks)
    special_tokens = {name: tokens_offset + i for i, name in enumerate(SPECIAL_TOKENS)}
    enc = tiktoken.Encoding(
        name="rustbpe",
        pat_str=pattern,
        mergeable_ranks=mergeable_ranks,
        special_tokens=special_tokens,
    )

    # Save tokenizer
    with open(tokenizer_pkl, "wb") as f:
        pickle.dump(enc, f)

    t1 = time.time()
    print(f"Tokenizer: trained in {t1 - t0:.1f}s, saved to {tokenizer_pkl}")

    # --- Build token_bytes lookup for BPB evaluation ---
    print("Tokenizer: building token_bytes lookup...")
    special_set = set(SPECIAL_TOKENS)
    token_bytes_list = []
    for token_id in range(enc.n_vocab):
        token_str = enc.decode([token_id])
        if token_str in special_set:
            token_bytes_list.append(0)
        else:
            token_bytes_list.append(len(token_str.encode("utf-8")))
    token_bytes_tensor = torch.tensor(token_bytes_list, dtype=torch.int32)
    torch.save(token_bytes_tensor, token_bytes_path)
    print(f"Tokenizer: saved token_bytes to {token_bytes_path}")

    # Sanity check
    test = "Hello world! Numbers: 123. Unicode: 你好"
    encoded = enc.encode_ordinary(test)
    decoded = enc.decode(encoded)
    assert decoded == test, f"Tokenizer roundtrip failed: {test!r} -> {decoded!r}"
    print(f"Tokenizer: sanity check passed (vocab_size={enc.n_vocab})")

# ---------------------------------------------------------------------------
# Runtime utilities (imported by train.py)
# ---------------------------------------------------------------------------

class Tokenizer:
    """Minimal tokenizer wrapper. Training is handled above."""

    def __init__(self, enc):
        self.enc = enc
        self.bos_token_id = enc.encode_single_token(BOS_TOKEN)

    @classmethod
    def from_directory(cls, tokenizer_dir=TOKENIZER_DIR):
        with open(os.path.join(tokenizer_dir, "tokenizer.pkl"), "rb") as f:
            enc = pickle.load(f)
        return cls(enc)

    def get_vocab_size(self):
        return self.enc.n_vocab

    def get_bos_token_id(self):
        return self.bos_token_id

    def encode(self, text, prepend=None, num_threads=8):
        if prepend is not None:
            prepend_id = prepend if isinstance(prepend, int) else self.enc.encode_single_token(prepend)
        if isinstance(text, str):
            ids = self.enc.encode_ordinary(text)
            if prepend is not None:
                ids.insert(0, prepend_id)
        elif isinstance(text, list):
            ids = self.enc.encode_ordinary_batch(text, num_threads=num_threads)
            if prepend is not None:
                for row in ids:
                    row.insert(0, prepend_id)
        else:
            raise ValueError(f"Invalid input type: {type(text)}")
        return ids

    def decode(self, ids):
        return self.enc.decode(ids)


def get_token_bytes(device="cpu"):
    path = os.path.join(TOKENIZER_DIR, "token_bytes.pt")
    with open(path, "rb") as f:
        return torch.load(f, map_location=device)


def _document_batches(split, tokenizer_batch_size=128):
    """Infinite iterator over document batches from parquet files."""
    parquet_paths = list_parquet_files()
    assert len(parquet_paths) > 0, "No parquet files found. Run prepare.py first."
    val_path = os.path.join(DATA_DIR, VAL_FILENAME)
    if split == "train":
        parquet_paths = [p for p in parquet_paths if p != val_path]
        assert len(parquet_paths) > 0, "No training shards found."
    else:
        parquet_paths = [val_path]
    epoch = 1
    while True:
        for filepath in parquet_paths:
            pf = pq.ParquetFile(filepath)
            for rg_idx in range(pf.num_row_groups):
                rg = pf.read_row_group(rg_idx)
                batch = rg.column('text').to_pylist()
                for i in range(0, len(batch), tokenizer_batch_size):
                    yield batch[i:i+tokenizer_batch_size], epoch
        epoch += 1


def make_dataloader(tokenizer, B, T, split, buffer_size=1000):
    """
    BOS-aligned dataloader with best-fit packing.
    Every row starts with BOS. Documents packed using best-fit to minimize cropping.
    When no document fits remaining space, crops shortest doc to fill exactly.
    100% utilization (no padding).
    """
    assert split in ["train", "val"]
    row_capacity = T + 1
    batches = _document_batches(split)
    bos_token = tokenizer.get_bos_token_id()
    doc_buffer = []
    epoch = 1

    def refill_buffer():
        nonlocal epoch
        doc_batch, epoch = next(batches)
        token_lists = tokenizer.encode(doc_batch, prepend=bos_token)
        doc_buffer.extend(token_lists)

    # Pre-allocate buffers: [inputs (B*T) | targets (B*T)]
    row_buffer = torch.empty((B, row_capacity), dtype=torch.long)
    cpu_buffer = torch.empty(2 * B * T, dtype=torch.long, pin_memory=True)
    gpu_buffer = torch.empty(2 * B * T, dtype=torch.long, device="cuda")
    cpu_inputs = cpu_buffer[:B * T].view(B, T)
    cpu_targets = cpu_buffer[B * T:].view(B, T)
    inputs = gpu_buffer[:B * T].view(B, T)
    targets = gpu_buffer[B * T:].view(B, T)

    while True:
        for row_idx in range(B):
            pos = 0
            while pos < row_capacity:
                while len(doc_buffer) < buffer_size:
                    refill_buffer()

                remaining = row_capacity - pos

                # Find largest doc that fits entirely
                best_idx = -1
                best_len = 0
                for i, doc in enumerate(doc_buffer):
                    doc_len = len(doc)
                    if doc_len <= remaining and doc_len > best_len:
                        best_idx = i
                        best_len = doc_len

                if best_idx >= 0:
                    doc = doc_buffer.pop(best_idx)
                    row_buffer[row_idx, pos:pos + len(doc)] = torch.tensor(doc, dtype=torch.long)
                    pos += len(doc)
                else:
                    # No doc fits — crop shortest to fill remaining
                    shortest_idx = min(range(len(doc_buffer)), key=lambda i: len(doc_buffer[i]))
                    doc = doc_buffer.pop(shortest_idx)
                    row_buffer[row_idx, pos:pos + remaining] = torch.tensor(doc[:remaining], dtype=torch.long)
                    pos += remaining

        cpu_inputs.copy_(row_buffer[:, :-1])
        cpu_targets.copy_(row_buffer[:, 1:])
        gpu_buffer.copy_(cpu_buffer, non_blocking=True)
        yield inputs, targets, epoch

# ---------------------------------------------------------------------------
# Evaluation (DO NOT CHANGE — this is the fixed metric)
# ---------------------------------------------------------------------------

@torch.no_grad()
def evaluate_bpb(model, tokenizer, batch_size):
    """
    Bits per byte (BPB): vocab size-independent evaluation metric.
    Sums per-token cross-entropy (in nats), sums target byte lengths,
    then converts nats/byte to bits/byte. Special tokens (byte length 0)
    are excluded from both sums.
    Uses fixed MAX_SEQ_LEN so results are comparable across configs.
    """
    token_bytes = get_token_bytes(device="cuda")
    val_loader = make_dataloader(tokenizer, batch_size, MAX_SEQ_LEN, "val")
    steps = EVAL_TOKENS // (batch_size * MAX_SEQ_LEN)
    total_nats = 0.0
    total_bytes = 0
    for _ in range(steps):
        x, y, _ = next(val_loader)
        loss_flat = model(x, y, reduction='none').view(-1)
        y_flat = y.view(-1)
        nbytes = token_bytes[y_flat]
        mask = nbytes > 0
        total_nats += (loss_flat * mask).sum().item()
        total_bytes += nbytes.sum().item()
    return total_nats / (math.log(2) * total_bytes)

# ---------------------------------------------------------------------------
# Triage & Model Setup
# ---------------------------------------------------------------------------

def download_model(repo_id="unsloth/gemma-4-e2b-it-GGUF", filename="gemma-4-E2B-it-Q4_K_M.gguf", source="auto"):
    """
    Ensure a model artifact exists locally.
    1. Checks Kaggle /input/ first (for notebook deployment, unless source=huggingface).
    2. Checks ~/.cache/autoresearch/models/ (for local dev).
    3. Optionally downloads from Kaggle CLI if source is auto/kaggle and a dataset slug is set.
    4. Downloads from Hugging Face if source is auto/huggingface.
    """
    source = normalize_source(source)
    os.makedirs(MODEL_DIR, exist_ok=True)
    local_filename = f"Edge-Triage-{filename}"
    model_path = os.path.join(MODEL_DIR, local_filename)

    # Path 1: Kaggle Input (Fastest for submission)
    # Note: Kaggle datasets are usually at /kaggle/input/<dataset-slug>/<filename>
    # We scan all subdirectories in /kaggle/input just in case.
    kaggle_base = os.getenv("KAGGLE_INPUT_DIR", "/kaggle/input")
    if source in {"auto", "kaggle"} and os.path.exists(kaggle_base):
        for root, dirs, files in os.walk(kaggle_base):
            if local_filename in files:
                kaggle_path = os.path.join(root, local_filename)
                print(f"Model: detected on Kaggle at {kaggle_path}")
                # Return the Kaggle path directly
                return kaggle_path

    # Path 2: Local Cache
    if os.path.exists(model_path):
        print(f"Model: {local_filename} already exists at {MODEL_DIR}")
        return model_path

    # Path 3: Optional Kaggle API fallback for judges/users without Hugging Face access.
    # Set EDGE_TRIAGE_KAGGLE_MODEL_DATASET=user/dataset-slug before running prepare.py.
    if source in {"auto", "kaggle"}:
        kaggle_dataset = os.getenv("EDGE_TRIAGE_KAGGLE_MODEL_DATASET")
        if kaggle_dataset:
            download_kaggle_dataset(kaggle_dataset, MODEL_DIR)
            kaggle_prefixed_path = os.path.join(MODEL_DIR, local_filename)
            kaggle_raw_path = os.path.join(MODEL_DIR, filename)
            if os.path.exists(kaggle_prefixed_path):
                print(f"Model: found {local_filename} from Kaggle dataset at {MODEL_DIR}")
                return kaggle_prefixed_path
            if os.path.exists(kaggle_raw_path):
                os.rename(kaggle_raw_path, model_path)
                print(f"Model: renamed Kaggle artifact to {local_filename}")
                return model_path
            if source == "auto":
                print(f"Model: Kaggle dataset did not contain {local_filename} or {filename}; falling back to Hugging Face...")
        elif source == "kaggle":
            raise RuntimeError(
                "Kaggle source selected but model artifact was not found. "
                "Attach model files as Kaggle Inputs or set EDGE_TRIAGE_KAGGLE_MODEL_DATASET=<user/dataset-slug>."
            )

        if source == "kaggle":
            raise RuntimeError(
                f"Kaggle source selected but {local_filename} was not found in attached Inputs or EDGE_TRIAGE_KAGGLE_MODEL_DATASET."
            )

    # Path 4: Hugging Face Download
    print(f"Model: downloading {filename} from {repo_id}...")
    temp_path = hf_hub_download(repo_id=repo_id, filename=filename, local_dir=MODEL_DIR)
    os.rename(temp_path, model_path)
    print(f"Model: renamed to {local_filename}")
    
    return model_path


def download_multimodal_projector(
    repo_id="unsloth/gemma-4-e4b-it-GGUF",
    filename="mmproj-F16.gguf",
    source="auto",
):
    """Ensure the mandatory Gemma vision multimodal projector exists locally."""
    return download_model(repo_id=repo_id, filename=filename, source=source)


def evaluate_triage(triage_fn, gold_set_path="data/gold_set.json", max_samples=None):
    """
    Evaluate a triage function against the gold set.
    Supports multimodal inputs by passing both text and image_path.
    """
    if not os.path.exists(gold_set_path):
        # Fallback to cache if local data not found
        gold_set_path = os.path.join(TRIAGE_DATA_DIR, "gold_set.json")

    if not os.path.exists(gold_set_path):
        print(f"Error: Gold set not found at {gold_set_path}. Run extraction first.")
        return None

    with open(gold_set_path, "r") as f:
        gold_set = json.load(f)

    if max_samples is not None:
        max_samples = max(1, int(max_samples))
        eval_set = gold_set[:max_samples]
    else:
        eval_set = gold_set

    y_true = []
    y_pred = []

    print(f"Evaluation: triaging {len(eval_set)} scenarios...")
    for i, item in enumerate(eval_set):
        print(f"[{i+1}/{len(eval_set)}] Processing: {item.get('image_id', 'unknown')}...", flush=True)
        scenario = item.get("text", "N/A")
        image_path = item.get("image_path")
        label = item["label_name"]

        # Call the provided triage function with multimodal support
        prediction = triage_fn(scenario, image_path=image_path)

        y_true.append(label)
        y_pred.append(prediction)
    # Calculate metrics
    accuracy = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="weighted")

    metrics = {
        "accuracy": accuracy,
        "f1": f1,
        "total": len(eval_set)
    }
    
    print(f"Evaluation Results: Accuracy={accuracy:.4f}, F1-Score={f1:.4f}")
    return metrics

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare data and tokenizer for autoresearch")
    parser.add_argument("--num-shards", type=int, default=10, help="Number of training shards to download (-1 = all). Val shard is always pinned.")
    parser.add_argument("--download-workers", type=int, default=8, help="Number of parallel download workers")
    parser.add_argument(
        "--source",
        choices=["auto", "huggingface", "kaggle"],
        default="auto",
        help="Artifact source preference: auto tries Kaggle inputs/cache/env first, then Hugging Face; huggingface skips Kaggle; kaggle refuses Hugging Face fallback.",
    )
    args = parser.parse_args()

    num_shards = MAX_SHARD if args.num_shards == -1 else args.num_shards

    print(f"Cache directory: {CACHE_DIR}")
    print()

    # Step 1: Download data
    download_data(num_shards, download_workers=args.download_workers, source=args.source)
    print()

    # Step 2: Train tokenizer
    train_tokenizer()
    print()

    # Step 3: Download model artifacts for triage
    download_model(source=args.source)
    download_multimodal_projector(source=args.source)
    print()
    print("Done! Ready for experiments.")
