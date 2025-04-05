import os

# === LLM ===
LLM_MODEL_TYPE = "Together"
LLM_MODEL_NAME = "meta-llama/Llama-3.3-70B-Instruct-Turbo"

# === Embedding model ===
EMBED_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"

# === Index paths ===
INDEX_DIR = "app/data/rag/indexes"
DESCRIPTION_INDEX_PATH = os.path.join(INDEX_DIR, "desc_index.faiss")
COMMENT_INDEX_PATH     = os.path.join(INDEX_DIR, "comment_index.faiss")

# === Metadata paths ===
META_DIR = "app/data/rag/meta"
DESCRIPTION_META_PATH = os.path.join(META_DIR, "desc_metadata.json")
COMMENT_META_PATH = os.path.join(META_DIR, "comment_metadata.json")

# === Corpus paths ===
CORPUS_DIR = "app/data/corpus"
RAW_CORPUS_PATH = os.path.join(CORPUS_DIR, "ph_raw_corpus.json")
ENHANCED_CORPUS_PATH = os.path.join(CORPUS_DIR, "ph_enhanced_corpus.json")
