import json
from app.utils.llm import standardize_concurrently
# Load the corpus into dictionary
with open("app/data/corpus/ph_raw_corpus.json", "r") as f:
    corpus = json.load(f) 

# Extract descriptions from the corpus + standardize each description 
descriptions = standardize_concurrently(corpus)
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