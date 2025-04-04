# handles loading + caching FAISS indexes and metadata in retrieval 
import faiss
import json
from typing import Tuple, List, Dict

from app.core.config import (
    DESCRIPTION_INDEX_PATH,
    COMMENT_INDEX_PATH,
    DESCRIPTION_META_PATH,
    COMMENT_META_PATH
)

# Internal cache for loaded indexes and metadata
_index_cache = {}

# helpers
def _load_faiss_index(index_path: str) -> faiss.Index:
    return faiss.read_index(index_path)

def _load_metadata(meta_path: str) -> List[Dict]:
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)

# based on entry type, load appropriate index and metadata -> return as tuple
def get_faiss_resources(entry_type: str) -> Tuple[faiss.Index, List[Dict]]:
    """
    Returns a tuple: (faiss index, metadata list) for given entry type.
    Supports 'description' or 'comment'.
    Loads and caches on first use.
    """
    if entry_type not in _index_cache:
        if entry_type == "description":
            index = _load_faiss_index(DESCRIPTION_INDEX_PATH)
            meta = _load_metadata(DESCRIPTION_META_PATH)
        elif entry_type == "comment":
            index = _load_faiss_index(COMMENT_INDEX_PATH)
            meta = _load_metadata(COMMENT_META_PATH)
        else:
            raise ValueError(f"Unknown entry_type: {entry_type}")
        
        _index_cache[entry_type] = (index, meta)

    return _index_cache[entry_type]