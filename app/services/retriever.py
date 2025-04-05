import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from dotenv import load_dotenv
from app.utils.expander import expand_query

load_dotenv()

from app.core.faiss_loader import get_faiss_resources
from app.core.config import EMBED_MODEL_NAME

# Initialize the embedding model globally
model = SentenceTransformer(EMBED_MODEL_NAME)

def expand_query(raw_query: str, n_expansions: int = 3) -> List[str]:
    """Expand a user query into semantically diverse paraphrases."""
    try:
        expanded_queries = expand_query(raw_query, n_expansions)
        print(f"Expanded query: {expanded_queries}")
        return expanded_queries # as list of n_expansions strings
    except Exception as e:
        print(f"⚠️ Query expansion failed: {e}")
        expanded_queries = [raw_query] # fallback to original query
    return expanded_queries
        
# Embedding user prompt query into dense vector -> single query
def embed_queries(queries: List[str]) -> np.ndarray:
    """Embed a list of query expansions into vectors."""
    return model.encode(
        queries,
        convert_to_numpy=True,
        normalize_embeddings=True, # must match index creation
        show_progress_bar=True,
        batch_size=16,
        num_workers=0
    )

def dedupe_by_company(results: List[tuple], meta: List[Dict], top_k: int = 5) -> List[Dict]:
    """
    Deduplicate results by company. Group matches (description + comments) under each company.
    For each company, keep all matches but sort companies by highest individual score.
    """
    company_groups = {}

    for idx, score in results:
        doc = meta[idx]
        doc_type = doc.get("type")
        
        # Identify company ID
        if doc_type == "description":
            company_id = doc["id"]
        elif doc_type == "comment":
            company_id = doc["meta"]["parentId"]
        else:
            continue  # skip unknown types
        
        # Initialize group if necessary
        if company_id not in company_groups:
            company_groups[company_id] = {
                "company_id": company_id,
                "max_score": float(score), # max score for this company
                "matches": []
            }

        # Always store matches and metadata
        company_groups[company_id]["matches"].append({
            "type": doc_type,
            "score": float(score),
            "metadata": doc
        })

        # Update score if this match is better
        if score > company_groups[company_id]["max_score"]:
            company_groups[company_id]["max_score"] = float(score)
            if doc_type == "description":
                company_groups[company_id]["metadata"] = doc  # keep richer info

    # Return top_k companies sorted by best individual match score
    return sorted(company_groups.values(), key=lambda x: x["max_score"], reverse=True)[:top_k]


def retrieve_top_k(raw_query: str, top_k: int = 5) -> List[Dict]:
    """
    Given a startup idea (query), retrieve top_k most relevant entries
    across both description and comment indexes, ranked by similarity.
    """
    # -----EXPAND & EMBED QUERY-----
    expanded_queries = expand_query(raw_query)  # expand raw query into n_expansions strings
    query_vecs = embed_queries(expanded_queries)  # embed all expansions

    # -----LOAD INDEXES-----
    desc_index, desc_meta = get_faiss_resources("description")
    comm_index, comm_meta = get_faiss_resources("comment")

    # -----SEARCH EACH EXPANSION-----
    all_results = []
    for vec in query_vecs:
        vec = vec.reshape(1, -1)  # (dim,) → (1, dim) for FAISS
        desc_scores, desc_indices = desc_index.search(vec, top_k)
        comm_scores, comm_indices = comm_index.search(vec, top_k)

        all_results.extend([(i, desc_scores[0][idx]) for idx, i in enumerate(desc_indices[0])])
        all_results.extend([(i, comm_scores[0][idx]) for idx, i in enumerate(comm_indices[0])])

    # -----DEDUPLICATE & SORT COMBINED RESULTS-----
    # Merge both sources and return unified top_k list
    combined_meta = desc_meta + comm_meta  # assume IDs don't overlap
    return dedupe_by_company(all_results, combined_meta, top_k=top_k)