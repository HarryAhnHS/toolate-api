import json, os, signal, sys
from tqdm import tqdm
from datetime import datetime
from app.utils.standardizer import standardize_batch
import random

INPUT_FILE = "app/data/corpus/ph_raw_corpus.json"
OUTPUT_FILE = "app/data/corpus/ph_enhanced_corpus.json"
BATCH_SIZE = 5
CACHE_FOLDER = "app/data/corpus/cache/"
CACHE_EVERY_N_BATCHES = 100

# --- Enhancement Version ---
# v1: initial enhancement
# v2: natural formatting and word limiting in prompts to improve output quality and prevent RAG embedding failures
CURRENT_ENHANCEMENT_VERSION = "v2"

# --- Global Variables ---
enhanced_corpus = [] # Global corpus for Ctrl+C save

def load_corpus(path):
    try:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            with open(path, "r") as f:
                return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        print(f"⚠️ No valid corpus found at {path}, starting fresh")
    return []

def save_corpus(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def save_checkpoint(data, batch_idx):
    os.makedirs(CACHE_FOLDER, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(CACHE_FOLDER, f"ph_enhanced_cp_batch{batch_idx}_{timestamp}.json")
    save_corpus(path, data)
    print(f"💾 Cached checkpoint at {path}")

def handle_exit(sig, frame):
    print("\n⚠️ Interrupted. Saving current progress...")
    save_corpus(OUTPUT_FILE, enhanced_corpus)
    print("✅ Saved. Exiting.")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)

def enhance_corpus():
    global enhanced_corpus

    total_raw_corpus = load_corpus(INPUT_FILE)
    enhanced_corpus = load_corpus(OUTPUT_FILE)

    # ENTRIES TO ENHANCE - never been enhanced yet
    # Build ID map of already enhanced entries
    enhanced_ids = {entry["id"] for entry in enhanced_corpus}
    # Filter: keep only entries that haven't yet been enhanced
    remaining = [entry for entry in total_raw_corpus if entry["id"] not in enhanced_ids]
    
    print("Out of a total of", len(total_raw_corpus), "entries in raw corpus:")
    print(f"🔍 {len(enhanced_corpus)} entries already enhanced.")
    print(f"🧠 Enhancing {len(remaining)} remaining entries...\n")

    seen_ids = set() # track seen IDs to avoid duplicates in this run
    total_batches = len(remaining) // BATCH_SIZE + (len(remaining) % BATCH_SIZE > 0)

    for batch_num in tqdm(range(1, total_batches + 1)):
        available = [entry for entry in remaining if entry["id"] not in seen_ids]
        if not available:
            break

        # Randomly sample BATCH_SIZE entries from available in remaining
        batch = random.sample(available, min(BATCH_SIZE, len(available)))

        try:
            print(f"🔍 Enhancing Batch {batch_num} ~ ['{batch[0]['id']}'... '{batch[-1]['id']}']")
            enhanced_batch = standardize_batch(batch, version=CURRENT_ENHANCEMENT_VERSION)
            enhanced_corpus.extend(enhanced_batch)

            # Update seen IDs to keep sample unique
            seen_ids.update(entry["id"] for entry in batch)

            # Rewrite to corpus at each batch
            save_corpus(OUTPUT_FILE, enhanced_corpus)
            print(f"✅ Appended and saved {len(enhanced_batch)} new entries!")
            print(f"✅ Total enhanced entries: {len(enhanced_corpus)}")

            # Save checkpoint every N batches - learnt the hard way...
            if batch_num % CACHE_EVERY_N_BATCHES == 0:
                save_checkpoint(enhanced_corpus, batch_num)
        except Exception as e:
            print(f"❌ Error in batch {batch_num}: {e}")
            continue

    print(f"\n✅ All done. Enhanced corpus saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    enhance_corpus()