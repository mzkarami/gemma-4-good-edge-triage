import os
from huggingface_hub import hf_hub_download

# Repo for Gemma 4 LiteRT models
REPO_ID = "litert-community/gemma-4-E2B-it-litert-lm"
# Official filename in the repo
SOURCE_FILENAME = "gemma-4-E2B-it.litertlm"
# Mandatory prefix for Hackathon compliance
LOCAL_FILENAME = f"Edge-Triage-{SOURCE_FILENAME}"
MODEL_DIR = os.path.expanduser("~/.cache/autoresearch/models")

def download_litert():
    os.makedirs(MODEL_DIR, exist_ok=True)
    dest_path = os.path.join(MODEL_DIR, LOCAL_FILENAME)
    
    if os.path.exists(dest_path):
        print(f"✅ LiteRT model already exists at {dest_path}")
        return
        
    print(f"Downloading {SOURCE_FILENAME} from {REPO_ID}...")
    try:
        # Download to a temporary path and then rename
        temp_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=SOURCE_FILENAME,
            local_dir=MODEL_DIR,
            local_dir_use_symlinks=False
        )
        os.rename(temp_path, dest_path)
        print(f"✅ Successfully downloaded and renamed LiteRT model to {dest_path}")
    except Exception as e:
        print(f"❌ Download failed: {e}")

if __name__ == "__main__":
    download_litert()
