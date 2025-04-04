# scripts/build_corpus_from_ph.py

import json
import os
from tqdm import tqdm

INPUT_FILE = "app/data/scrapes/ph_ai_scrape.json"
OUTPUT_FILE = "app/data/corpus/ph_raw_corpus.json"

# extract tags from post
def extract_tags(topics):
    if not topics: return []
    return [t["node"]["name"].lower() for t in topics.get("edges", [])]

# extract comments from post
def extract_comments(comment_edges):
    if not comment_edges: return []
    return [c["node"]["body"].strip() for c in comment_edges.get("edges", [])]

def generate_corpus_entry(post):
    post_id = f"ph_{post['id']}"
    entry = {
        "type": "description",
        "id": post_id,
        "text": post["description"].strip(),
        "meta": {
            "name": post["name"],
            "url": post["url"],
            "source": "producthunt",
            "createdAt": post["createdAt"],
            "tags": extract_tags(post.get("topics"))
        }
    }

    # Separate comments into their own entries
    comments = []
    for i, body in enumerate(extract_comments(post.get("comments", {}))):
        if not body.strip():
            continue
        comments.append({
            "type": "comment",
            "id": f"{post_id}_c{i+1}",
            "text": body.strip(),
            "meta": {
                "parent": post_id # to group chunks by post
            }
        })

    return [entry], comments

def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(INPUT_FILE, "r") as f:
        posts = json.load(f)

    full_corpus = []
    # Process each post with tqdm progress bar
    for post in tqdm(posts, desc="Processing posts"):
        entries, comments = generate_corpus_entry(post)
        full_corpus.extend(entries)
        full_corpus.extend(comments)

    # Write completed raw corpus to output file
    with open(OUTPUT_FILE, "w") as f:
        json.dump(full_corpus, f, indent=2)

    print(f"\n✅ Corpus written to {OUTPUT_FILE} with {len(full_corpus)} entries")

if __name__ == "__main__":
    main()