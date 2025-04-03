import gc
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from app.utils.llm import standardize 

import os
from dotenv import load_dotenv

load_dotenv()
gc.collect()

# Load the corpus into dictionary
with open("app/data/corpus.json", "r") as f:
    corpus = json.load(f) 

# Extract descriptions from the corpus + standardize each description
print(f"Standardizing {len(corpus)} descriptions...")  
descriptions = [standardize(c["description"]) for c in corpus]
# descriptions = standardize_concurrently(raw_descriptions)
print(f"Standardized {len(descriptions)} descriptions, {descriptions[0:2]}")

# Load the model
st_model = os.getenv("ST_MODEL")
model = SentenceTransformer(st_model)
embeddings = model.encode(
    descriptions,
    show_progress_bar=True,
    batch_size=16,
    convert_to_numpy=True,
    normalize_embeddings=True,
    num_workers=0
)

# Save the embeddings
np.save("app/data/corpus_embeddings.npy", embeddings)

# Build the index using L2 distance - euclidean distance
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(np.array(embeddings))

# Save the searchable index
faiss.write_index(index, "app/data/corpus_index.faiss")

print(f"Successfully embedded {len(descriptions)} startups and saved index.")