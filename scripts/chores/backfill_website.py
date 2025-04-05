import json

ENHANCED_PATH = "app/data/corpus/ph_enhanced_corpus.json"
RAW_PATH = "app/data/corpus/ph_raw_corpus.json"
OUTPUT_PATH = "app/data/corpus/ph_enhanced_corpus_with_websites.json"

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def build_id_to_website_map(raw_entries):
    id_to_website = {}
    for entry in raw_entries:
        entry_id = entry.get("id")
        website = entry.get("website") or entry.get("meta", {}).get("website")
        if entry_id and website:
            id_to_website[entry_id] = website
    return id_to_website

def enrich_with_website(enhanced_entries, id_to_website):
    enriched = []
    for entry in enhanced_entries:
        if entry["type"] == "description":
            website = id_to_website.get(entry["id"])
            if website:
                entry["meta"]["website"] = website
        elif entry["type"] == "comment":
            parent_id = entry.get("meta", {}).get("parent_id")
            website = id_to_website.get(parent_id)
            if website:
                entry["meta"]["parent_website"] = website
        enriched.append(entry)
    return enriched

def main():
    enhanced_entries = load_json(ENHANCED_PATH)
    raw_entries = load_json(RAW_PATH)
    
    id_to_website = build_id_to_website_map(raw_entries)
    enriched_entries = enrich_with_website(enhanced_entries, id_to_website)

    save_json(enriched_entries, OUTPUT_PATH)
    print(f"✅ Enriched corpus saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()