from together import Together
from concurrent.futures import ThreadPoolExecutor
from typing import List

import os
from dotenv import load_dotenv

load_dotenv()

# Standardize the description/input prior to embedding
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

# USER PROMPTS
IDEA_PROMPT_TEMPLATE = """
Rewrite the following startup idea into a structured, technical product description.

Startup Idea:
\"\"\"{idea}\"\"\"
"""

# CORPUS PROMPTS
CORPUS_DESCRIPTION_PROMPT_TEMPLATE = """
You're an AI assistant helping analyze early-stage AI startups. Based on the following raw Product Hunt data, rewrite the startup description into a clear, concise, and technical product summary.

Include:
- What the product does
- Target users or use case
- Key features or technologies
- Unique value prop if available

Startup Name: {name}
Startup Tags: {tags}

Raw Description:
\"\"\"{description}\"\"\"
"""

CORPUS_COMMENT_PROMPT_TEMPLATE = """
You're analyzing community feedback on a startup.

Below is a user comment about a new AI product, along with basic product info. Rewrite the comment to clearly explain the insight or opinion, using the product context when needed.

Startup Name: {name}
Startup Tags: {tags}
Startup Description: {description}

User Comment:
\"\"\"{comment}\"\"\"

Rewrite:
"""

# STANDARDIZATION FUNCTIONS
def standardize_entry(entry: dict) -> str:
    match entry["type"]:
        case "description":
            description = entry["text"]
            name = entry["meta"]["name"]
            tags = ", ".join(entry["meta"].get("tags", []))
            prompt = CORPUS_DESCRIPTION_PROMPT_TEMPLATE.format(name=name, description=description, tags=tags)
        case "comment":
            comment = entry["text"]
            prompt = CORPUS_COMMENT_PROMPT_TEMPLATE.format(comment=comment)
        case _:
            raise ValueError("Invalid type. Must be a supported entry type.")
    
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()

def standardize_idea(idea: str) -> str:
    prompt = IDEA_PROMPT_TEMPLATE.format(idea=idea)
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()

# use ThreadPoolExecutor to standardize descriptions concurrently
def concurrently(standardize_fn: function, entries: List[dict]) -> List[str]:
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(standardize_fn, entries))
    return results