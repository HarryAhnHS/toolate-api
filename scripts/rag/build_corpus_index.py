import json
import os
import faiss
import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

# CONFIG
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL")
CORPUS_FILE = "app/data/corpus/test_enhanced_corpus.json"
OUTPUT_DIR = "app/data/rag/indexes"

# Store paths for index, and metadata based on keyed by type
ENTRY_PATHS = [{
    "type": "description",
    "index_path": os.path.join(OUTPUT_DIR, "desc_index.faiss"),
    "meta_path": os.path.join(OUTPUT_DIR, "desc_metadata.json")
}, {
    "type": "comment",
    "index_path": os.path.join(OUTPUT_DIR, "comment_index.faiss"),
    "meta_path": os.path.join(OUTPUT_DIR, "comment_metadata.json")
}]

# UTILS
def load_corpus(file_path: str) -> List[Dict]: # load ENHANCEDcorpus from file
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, path): # save metadata for future reference
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def embed_texts(texts: List[str], model: SentenceTransformer) -> np.ndarray: # convert into dense vectors
    return np.array(model.encode(
        texts,
        show_progress_bar=True,
        batch_size=16,
        convert_to_numpy=True,
        normalize_embeddings=True,
        num_workers=0
    ))

def build_faiss_index(embeddings: np.ndarray):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index

def extract_entries(corpus: List[Dict], entry_type: str): # use this to extract entries by type ("Comment" or "Description")
    texts = []
    metas = []
    for entry in corpus:
        if entry.get("type") == entry_type and entry.get("isEnhanced"): # isEnhanced check is pointless currently, but keep for scaling
            texts.append(entry["standardized"])
            metas.append(entry)
    return texts, metas

# MAIN PIPELINE - extract, embed, build index, save metadata
def embed_and_index():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    corpus = load_corpus(CORPUS_FILE)
    model = SentenceTransformer(EMBED_MODEL_NAME)

    # process each entry type
    for entry in ENTRY_PATHS:
        print(f"\n📦 Starting processing for '{entry['type']}' entries...")
        texts, metas = extract_entries(corpus, entry['type'])
        print(f"Found {len(texts)} {entry['type']} entries.")

        print("Embedding...")
        embeddings = embed_texts(texts, model)

        print("Building FAISS index...")
        index = build_faiss_index(embeddings)

        print("Saving index and metadata...")
        faiss.write_index(index, entry["index_path"])
        save_json(metas, entry["meta_path"])

        print(f"Done: {entry['index_path']} | {entry['meta_path']}")

if __name__ == "__main__":
    embed_and_index()