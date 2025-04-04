# services/retrieval.py

import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

from core.faiss_loader import get_faiss_resources
from core.config import EMBED_MODEL_NAME
# Initialize the embedding model globally
model = SentenceTransformer(EMBED_MODEL_NAME)

# Embedding user prompt query into dense vector -> single query
def embed_query(text: str) -> np.ndarray:
    """Embed a single user query into a vector."""
    return model.encode(
        [text],
        convert_to_numpy=True,
        normalize_embeddings=True, # must be consistent with index creation = for cosine or L2 distance
    )[0]

def retrieve_top_k(query: str, top_k: int = 5) -> Dict[str, List[Dict]]:
    """
    Given a startup idea (query), retrieve top_k most similar
    description and comment entries from the FAISS indexes.
    """
    # -----EMBEDDING USER QUERY-----
    # reshape from (dim,) to (1, dim) for FAISS search
    query_vec = embed_query(query).reshape(1, -1)

    # -----SEARCHING-----
    # Load pre-builtFAISS indexes and metadata
    desc_index, desc_meta = get_faiss_resources("description")
    comm_index, comm_meta = get_faiss_resources("comment")
    # Search both indexes
    desc_scores, desc_indices = desc_index.search(query_vec, top_k)
    comm_scores, comm_indices = comm_index.search(query_vec, top_k)

    # -----PACKAGING RESULTS-----
    # Package results
    descriptions = [desc_meta[i] | {"score": float(desc_scores[0][idx])} for idx, i in enumerate(desc_indices[0])]
    comments = [comm_meta[i] | {"score": float(comm_scores[0][idx])} for idx, i in enumerate(comm_indices[0])]

    return {
        "descriptions": descriptions,
        "comments": comments
    }
