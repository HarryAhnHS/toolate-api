import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from dotenv import load_dotenv
import json
from app.llm.expander import expand_query
from app.llm.evaluator import calculate_uniqueness

load_dotenv()

from app.core.faiss_loader import get_faiss_resources
from app.core.config import EMBED_MODEL_NAME, RAW_CORPUS_PATH

# Initialize the embedding model globally
model = SentenceTransformer(EMBED_MODEL_NAME)

def create_query_expansions(raw_query: str, n_expansions: int = 2) -> List[str]:
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
def embed_queries(queries: List[str], weights: List[float]) -> np.ndarray:
    """Embed a list of query expansions into vectors."""
    return model.encode(
        queries,
        weights=weights,
        convert_to_numpy=True, 
        normalize_embeddings=True, # must match index creation
        show_progress_bar=True,
        batch_size=16,
        num_workers=0
    )

def extract_product_description_meta(id: str) -> Dict:
    """
    Extract product metadata from a comment entry using raw_corpus (not enhanced).
    In raw_corpus, all comments have a corresponding description entry, 
    but not necessarily in enhanced_corpus, as we are randomly batching comments and descriptions.
    """
    total_corpus = json.load(open(RAW_CORPUS_PATH))
    for entry in total_corpus:
        if entry.get("company_id") == id:
            return entry

def dedupe_by_company(
    results: List[tuple], 
    desc_meta: List[Dict], 
    comm_meta: List[Dict], 
    top_k: int = 5
) -> List[Dict]:
    """
    Group matches by companyId. Aggregate scores and return top_k unique companies.
    """
    company_groups = {}

    print(f"Deduplicating {len(results)} results...")
    for idx, score, source in results:
        doc = desc_meta[idx] if source == "description" else comm_meta[idx]
        company_id = doc.get("company_id")
        source_id = doc.get("id")

        if not company_id:
            continue

        # Initialize company group if it doesn't exist
        # Company groups are stored as a dictionary, each containing:
        # - company_id: company ID
        # - product_meta: metadata for the company - scraped once
        # - min_score: minimum similarity score
        # - match_percent: percentage of matches found in the company
        # - matches: list of matches
        if company_id not in company_groups:
            company_groups[company_id] = {
                "company_id": company_id,
                "product_meta": doc if source == "description" else extract_product_description_meta(company_id),
                "min_score": float(score),
                "matches": [],

                # metrics that are calculated after deduplication
                "match_percent": 0,
                "avg_score": 0,
            }

        # Matches are stored as a list of dictionaries, each containing:
        # - type: "description" or "comment"
        # - score: similarity score
        # - match_meta: metadata for the matched document
        # Use a mapping from source_id to match index for fast lookup
        existing_ids = {match["match_meta"]["id"]: idx for idx, match in enumerate(company_groups[company_id]["matches"])}

        if source_id in existing_ids:
            existing_match = company_groups[company_id]["matches"][existing_ids[source_id]]
            # Keep the lower (better) L2 score
            if score < existing_match["score"]:
                existing_match["score"] = float(score)
                existing_match["match_meta"] = doc
        else:
            company_groups[company_id]["matches"].append({
                "type": source,
                "score": float(score),
                "match_meta": doc
            })

            

        # Update minimum score if current match is better
        if score < company_groups[company_id]["min_score"]:
            company_groups[company_id]["min_score"] = float(score)

    # Calculate avg_score and match_percent for each company
    # Normalize l2 distance with dynamic range and invert to get match_percent
    all_l2 = [match["score"] for company in company_groups.values() for match in company["matches"]]
    L2_MIN = min(all_l2)
    L2_MAX = max(all_l2)

    for company in company_groups.values():
        avg_l2 = sum(m["score"] for m in company["matches"]) / len(company["matches"])
        company["avg_score"] = avg_l2
        
        # Normalize with batch range
        if L2_MAX != L2_MIN:
            normalized = (avg_l2 - L2_MIN) / (L2_MAX - L2_MIN)
        else:
            normalized = 0.0  # all the same
        company["match_percent"] = round(1.0 - normalized, 4)

    # Return top_k companies sorted by minimum score + uniqueness score
    return sorted(company_groups.values(), key=lambda x: x["match_percent"], reverse=True)[:top_k], calculate_uniqueness(company_groups.values(), top_k)


def retrieve_top_k(raw_query: str, top_k: int = 5) -> List[Dict]:
    """
    Given a startup idea (query), retrieve top_k most relevant entries
    across both description and comment indexes, ranked by similarity.
    """
    # -----EXPAND & EMBED QUERY-----
    expanded_queries = create_query_expansions(raw_query)  # expand raw query into n_expansions strings
    queries = [raw_query] + expanded_queries
    weights = [2.0] + [1.0] * len(expanded_queries)
    query_vecs = embed_queries(queries, weights)  # embed all expansions

    # -----LOAD INDEXES-----
    desc_index, desc_meta = get_faiss_resources("description")
    comm_index, comm_meta = get_faiss_resources("comment")

    # -----SEARCH EACH EXPANSION-----
    all_results = []
    search_limit = top_k * 2  # to increase candidate pool and avoid company overlap

    for vec in query_vecs:
        vec = vec.reshape(1, -1)  # (dim,) → (1, dim) for FAISS
        desc_scores, desc_indices = desc_index.search(vec, search_limit)
        comm_scores, comm_indices = comm_index.search(vec, search_limit)
        for idx, i in enumerate(desc_indices[0]):
            all_results.append((i, desc_scores[0][idx], "description"))

        for idx, i in enumerate(comm_indices[0]):
            all_results.append((i, comm_scores[0][idx], "comment"))


    # -----DEDUPLICATE & SORT COMBINED RESULTS-----
    # Merge both sources and return unified top_k list
    return dedupe_by_company(all_results, desc_meta, comm_meta, top_k=top_k)