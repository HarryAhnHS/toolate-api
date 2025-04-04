import json
import os
from datetime import datetime, timezone

INPUT_PATH = "app/data/corpus/ph_enhanced_corpus.json"
BACKUP_PATH = "app/data/corpus/ph_enhanced_corpus_backup.json"
VERSION = "v1"

def main():
    with open(INPUT_PATH, "r") as f:
        data = json.load(f)

    updated = 0
    for entry in data:
        if not entry.get("isEnhanced"):
            entry["isEnhanced"] = True
            entry["enhancementVersion"] = VERSION
            entry["enhancedAt"] = datetime.now(timezone.utc).isoformat()
            updated += 1

    print(f"🔧 Backfilling metadata on {updated} entries...")

    # Optional: create a backup before overwriting
    os.makedirs(os.path.dirname(BACKUP_PATH), exist_ok=True)
    with open(BACKUP_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"📦 Backup saved to {BACKUP_PATH}")

    # Overwrite the original file
    with open(INPUT_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Overwrote original file with {len(data)} entries updated.")

if __name__ == "__main__":
    main()
