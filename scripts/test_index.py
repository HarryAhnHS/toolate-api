import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
from app.utils.llm import standardize

load_dotenv()

# Load corpus
with open("app/data/corpus.json", "r") as f:
    corpus = json.load(f)

# Load FAISS index
index = faiss.read_index("app/data/corpus_index.faiss")

# Load embedding model
st_model = os.getenv("ST_MODEL")
model = SentenceTransformer(st_model)

# Ask for input
raw_input = input("Enter your startup idea: ")
user_idea = standardize(raw_input, type="idea")

# Embed the query
query_embedding = model.encode([user_idea])
query_embedding = np.array(query_embedding).astype("float32")

# Perform semantic search
k = 2
D, I = index.search(query_embedding, k)

# Print results
print("\nTop Similar Startups:\n")
for rank, idx in enumerate(I[0]):
    result = corpus[idx]
    print(f"{rank+1}. {result['name']} ({result['source']})")
    print(f"   Standardized Description: {result['standardized_description']}")
    print(f"   URL: {result['url']}")
    print(f"   Distance: {D[0][rank]:.4f}\n")
