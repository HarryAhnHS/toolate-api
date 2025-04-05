# not used
from typing import List, Dict
import numpy as np

from typing import List, Dict
import numpy as np

def calculate_uniqueness(top_k_companies: List[Dict], expected_k: int = 5) -> int:
    if not top_k_companies:
        return 100


    # Convert L2 distances into similarity scores
    def sim(d): return np.exp(-d) # exponential decay making distant matches drop off faster

    for company in top_k_companies:
        chunk_scores = [match["score"] for match in company["matches"]]  # these are L2 distances
        company["avg_score"] = np.mean(chunk_scores)  # <- new per-company signal

    avg_sim = np.mean([sim(c["avg_score"]) for c in top_k_companies]) # base uniqueness score
    max_sim = max(sim(c["min_score"]) for c in top_k_companies)

    combined = 0.2 * max_sim + 0.8 * avg_sim

    uniqueness = int((1 - combined) * 100)
    return max(0, min(100, uniqueness))