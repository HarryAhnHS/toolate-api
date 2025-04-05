import json
import os

#cleanup
import gc
import torch

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict

from app.core.config import EMBED_MODEL_NAME, INDEX_DIR, META_DIR, DESCRIPTION_INDEX_PATH, COMMENT_INDEX_PATH, DESCRIPTION_META_PATH, COMMENT_META_PATH

META_OUTPUT_DIR = META_DIR
INDEX_OUTPUT_DIR = INDEX_DIR

INDEX_SCHEMA = [{
    "type": "description",
    "index_path": DESCRIPTION_INDEX_PATH,
    "meta_path": DESCRIPTION_META_PATH
}, {
    "type": "comment",
    "index_path": COMMENT_INDEX_PATH,
    "meta_path": COMMENT_META_PATH
}]
# test file with about 1300 entries - 521 descriptions, 785 comments
# CORPUS_FILE = "app/data/corpus/test_enhanced_corpus.json"

# production file with about 3000 entries - 1495 descriptions, 2248 comments
CORPUS_FILE = "app/data/corpus/ph_enhanced_corpus.json"


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
    # Make output directories if they don't exist
    os.makedirs(META_OUTPUT_DIR, exist_ok=True)
    os.makedirs(INDEX_OUTPUT_DIR, exist_ok=True)

    corpus = load_corpus(CORPUS_FILE)
    model = SentenceTransformer(EMBED_MODEL_NAME)

    # process each entry type
    for entry in INDEX_SCHEMA:
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
    
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


if __name__ == "__main__":
    embed_and_index()