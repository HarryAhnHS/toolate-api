import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Load the corpus into dictionary
with open("app/data/corpus.json", "r") as f:
    corpus = json.load(f) 

# Extract descriptions from the corpus
descriptions = [c["description"] for c in corpus]

# Load the model
model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
embeddings = model.encode(descriptions)

np.save("app/data/corpus_embeddings.npy", embeddings)

# Build the index using L2 distance - euclidean distance
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(np.array(embeddings))

# Save the searchable index
faiss.write_index(index, "app/data/corpus_index.faiss")

print(f"Successfully embedded {len(descriptions)} startups and saved index.")