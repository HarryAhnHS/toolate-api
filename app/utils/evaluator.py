from typing import List, Dict
import numpy as np

from typing import List, Dict
import numpy as np

def calculate_uniqueness(top_k_companies: List[Dict], expected_k: int = 5) -> int:
    if not top_k_companies:
        return 100


    # Convert L2 distances into similarity scores
    def sim(d): return np.exp(-d) # exponential decay making distant matches drop off faster

    max_sim = max(sim(c["min_score"]) for c in top_k_companies)
    avg_sim = np.mean([sim(c["min_score"]) for c in top_k_companies])

    combined_sim = 0.4 * max_sim + 0.6 * avg_sim

    uniqueness = int((1 - combined_sim) * 100)
    return max(0, min(100, uniqueness))