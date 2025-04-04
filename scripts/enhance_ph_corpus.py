# enhance_corpus.py

import json, os, signal, sys
from tqdm import tqdm
from app.utils.standardizer import standardize_batch

INPUT_FILE = "app/data/corpus/ph_raw_corpus.json"
OUTPUT_FILE = "app/data/corpus/ph_enhanced_corpus.json"
BATCH_SIZE = 5

# --- Enhancement Version ---
# v1: initial enhancement
# v2: natural formatting and word limiting in prompts to improve output quality and prevent RAG embedding failures
CURRENT_ENHANCEMENT_VERSION = "v2"

# Global corpus for Ctrl+C save
enhanced_corpus = []

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

def handle_exit(sig, frame):
    print("\n⚠️ Interrupted. Saving current progress...")
    save_corpus(OUTPUT_FILE, enhanced_corpus)
    print("✅ Saved. Exiting.")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)

def enhance_corpus():
    global enhanced_corpus

    raw_corpus = load_corpus(INPUT_FILE)
    enhanced_corpus = load_corpus(OUTPUT_FILE)

    # Use ID map to dedupe
    enhanced_ids = {e["id"] for e in enhanced_corpus}

    # ENTRIES TO ENHANCE - never been enhanced yet
    remaining = [entry for entry in raw_corpus if not entry.get("isEnhanced")]
    
    print("Out of a total of", len(raw_corpus), "entries in raw corpus:")
    print(f"🔍 {len(enhanced_ids)} entries already enhanced.")
    print(f"🧠 Enhancing {len(remaining)} remaining entries...\n")

    for i in tqdm(range(0, len(remaining), BATCH_SIZE)):
        batch = remaining[i:i + BATCH_SIZE]
        try:
            print(f"🔍 Enhancing Batch {(i / BATCH_SIZE) + 1} ~ ['{batch[0]['id']}'... '{batch[-1]['id']}']")
            enhanced_batch = standardize_batch(batch, version=CURRENT_ENHANCEMENT_VERSION)
            enhanced_corpus.extend(enhanced_batch)

            save_corpus(OUTPUT_FILE, enhanced_corpus)  # ✅ rewrite at each batch
            print(f"✅ Appended and saved {len(enhanced_batch)} new entries!")
            print(f"✅ Total enhanced entries: {len(enhanced_corpus)}")
        except Exception as e:
            print(f"❌ Error in batch {i - BATCH_SIZE + 1}: {e}")
            continue

    print(f"\n✅ All done. Enhanced corpus saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    enhance_corpus()