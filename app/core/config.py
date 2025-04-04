import os

# === LLM ===
LLM_MODEL_NAME = "gpt-4o-mini"

# === Embedding model ===
EMBED_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"

# === Index paths ===
DATA_DIR = "app/data/rag/indexes"
DESCRIPTION_INDEX = os.path.join(DATA_DIR, "desc_index.faiss")
COMMENT_INDEX     = os.path.join(DATA_DIR, "comment_index.faiss")
DESC_META         = os.path.join(DATA_DIR, "desc_metadata.json")
COMM_META         = os.path.join(DATA_DIR, "comment_metadata.json")