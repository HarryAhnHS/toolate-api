import gc
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from app.utils.llm import standardize_concurrently

import os
from dotenv import load_dotenv

load_dotenv()
gc.collect()

# Load the corpus into dictionary
with open("app/data/corpus.json", "r") as f:
    corpus = json.load(f) 

# Extract descriptions from the corpus + standardize each description
print(f"Standardizing {len(corpus)} descriptions...")  
raw_descriptions = [c["description"] for c in corpus]
descriptions = standardize_concurrently(raw_descriptions)
print(f"Successfully standardized {len(corpus)} descriptions!")
print(f"Descriptions: {descriptions[0:1]}")

# Update corpus with standardized summaries if they don't exist or are different
print("Updating corpus with standardized descriptions...")
for i, entry in enumerate(corpus):
    entry["standardized_description"] = descriptions[i]
print("Successfully updated corpus with standardized descriptions!")

# Save the updated corpus back to JSON
with open("app/data/corpus.json", "w") as f:
    json.dump(corpus, f, indent=2)

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