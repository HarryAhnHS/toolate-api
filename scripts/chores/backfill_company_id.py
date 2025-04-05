import json

INPUT_FILE = "app/data/corpus/ph_enhanced_corpus.json"
OUTPUT_FILE = "app/data/corpus/ph_enhanced_corpus_with_company_id.json"

def append_company_id(corpus):
    for entry in corpus:
        if entry["type"] == "description":
            entry["company_id"] = entry["id"]
        elif entry["type"] == "comment":
            entry["company_id"] = entry["meta"]["parent_id"]
    return corpus

# Example usage
if __name__ == "__main__":
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated_data = append_company_id(data)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)
