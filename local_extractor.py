import os
import json
import pandas as pd
from PIL import Image
import io
from tqdm import tqdm
import hashlib

# Configuration
NUM_SAMPLES = 50
DATA_DIR = "data"
IMAGE_DIR = os.path.join(DATA_DIR, "images")
GOLD_SET_PATH = os.path.join(DATA_DIR, "gold_set.json")

# Label mapping from MEDIC dataset features
LABEL_NAMES = [
    'affected_injured_or_dead_people', 
    'infrastructure_and_utility_damage', 
    'not_humanitarian', 
    'rescue_volunteering_or_donation_effort'
]

def extract_from_local_parquet():
    """
    Reads MEDIC parquet files and extracts images/labels.
    Scans local 'data/' first, falls back to global cache (~/.cache/autoresearch/data).
    Uses md5 hash of image path as a unique identifier.
    """
    os.makedirs(IMAGE_DIR, exist_ok=True)
    
    # 1. Determine search paths
    search_dirs = [DATA_DIR]
    try:
        from prepare import DATA_DIR as GLOBAL_DATA_DIR
        if os.path.exists(GLOBAL_DATA_DIR) and GLOBAL_DATA_DIR not in search_dirs:
            search_dirs.append(GLOBAL_DATA_DIR)
    except ImportError:
        # Fallback if prepare.py is not available
        cache_fallback = os.path.join(os.path.expanduser("~"), ".cache", "edge-triage", "data")
        if os.path.exists(cache_fallback):
            search_dirs.append(cache_fallback)

    # 2. Collect all parquet files from all search directories
    parquet_files = []
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        files = [os.path.join(d, f) for f in os.listdir(d) if f.endswith(".parquet")]
        parquet_files.extend(files)
    
    if not parquet_files:
        print(f"Error: No .parquet files found in searched directories: {search_dirs}")
        return

    gold_set = []
    seen_hashes = set()
    
    print(f"Data: Extracting up to {NUM_SAMPLES} samples from {len(parquet_files)} files...")
    print(f"Data: Search paths: {search_dirs}")
    
    for p_file in parquet_files:
        if len(gold_set) >= NUM_SAMPLES:
            break
            
        print(f"Processing {p_file}...")
        try:
            df = pd.read_parquet(p_file)
        except Exception as e:
            print(f"  - Failed to read {p_file}: {e}")
            continue

        # Skip files that are not multimodal (e.g. Karpathy text shards)
        if "image" not in df.columns or "image_path" not in df.columns:
            print(f"  - Skipping {p_file}: No 'image' or 'image_path' columns found.")
            continue
            
        file_samples = 0
        for _, row in tqdm(df.iterrows(), total=len(df), desc=f"Extracting {os.path.basename(p_file)}"):
            if len(gold_set) >= NUM_SAMPLES:
                break
                
            raw_path = str(row["image_path"])
            image_hash = hashlib.md5(raw_path.encode()).hexdigest()
            image_data = row["image"]
            human_label_idx = row["humanitarian"]
            
            # Use hash as unique ID
            if image_hash in seen_hashes:
                continue
            
            try:
                if isinstance(image_data, dict) and "bytes" in image_data:
                    img_bytes = image_data["bytes"]
                elif isinstance(image_data, bytes):
                    img_bytes = image_data
                else:
                    continue

                if img_bytes is None:
                    continue

                # Save the image using hash as filename
                image_filename = f"{image_hash}.jpg"
                image_path = os.path.join(IMAGE_DIR, image_filename)
                
                img = Image.open(io.BytesIO(img_bytes))
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(image_path, "JPEG")

                # Map integer label to string
                label_name = LABEL_NAMES[human_label_idx] if human_label_idx < len(LABEL_NAMES) else "unknown"

                gold_set.append({
                    "image_id": image_hash,
                    "image_path": image_path,
                    "text": "N/A", 
                    "label_name": label_name,
                    "event": row["event_name"],
                    "disaster_types": row["disaster_types"]
                })
                seen_hashes.add(image_hash)
                
            except Exception as e:
                continue
                
    with open(GOLD_SET_PATH, "w") as f:
        json.dump(gold_set, f, indent=2)
        
    print(f"Data: Successfully extracted {len(gold_set)} unique samples to {GOLD_SET_PATH}")

if __name__ == "__main__":
    extract_from_local_parquet()
