import json
import os
import faiss
import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from typing import List, Dict

from app.core.config import EMBED_MODEL_NAME, DATA_DIR, DESCRIPTION_INDEX, COMMENT_INDEX, DESC_META, COMM_META


ENTRY_PATHS = [{
    "type": "description",
    "index_path": DESCRIPTION_INDEX,
    "meta_path": DESC_META
}, {
    "type": "comment",
    "index_path": COMMENT_INDEX,
    "meta_path": COMM_META
}]
CORPUS_FILE = "app/data/corpus/test_enhanced_corpus.json"
OUTPUT_DIR = DATA_DIR

# UTILS
def load_corpus(file_path: str) -> List[Dict]: # load ENHANCEDcorpus from file
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, path): # save metadata for future reference
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# Embedding all texts entries into dense vectors -> multiple queries
def embed_texts(texts: List[str], model: SentenceTransformer) -> np.ndarray: # convert into dense vectors
    return np.array(model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True, # for cosine or L2 distance

        # these params are for multiple query handling
        show_progress_bar=True,
        batch_size=16,
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