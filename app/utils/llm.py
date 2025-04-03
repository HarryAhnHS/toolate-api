from together import Together
from concurrent.futures import ThreadPoolExecutor
from typing import List
from functools import partial

import os
from dotenv import load_dotenv

load_dotenv()

# Standardize the description/input prior to embedding
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

CORPUS_PROMPT_TEMPLATE = """
Rewrite the following startup idea into a structured, technical product description (5 sentences maximum).

You MUST focus on:
- Core functionality and technical capabilities (not marketing)
- Specific features or APIs (what it lets users actually *do*)
- Target users or industries
- Differentiators: how this startup compares to similar tools
- DO NOT mention funding, YC, launch batch, partners, or historical facts

Startup Idea:
\"\"\"{idea}\"\"\"
"""

IDEA_PROMPT_TEMPLATE = """
Rewrite the following startup idea into a structured, technical product description.

Startup Idea:
\"\"\"{idea}\"\"\"
"""
def standardize(raw_str: str, type: str = "corpus") -> str:
    if type == "corpus":
        prompt = CORPUS_PROMPT_TEMPLATE.format(idea=raw_str)
    elif type == "idea":
        prompt = IDEA_PROMPT_TEMPLATE.format(idea=raw_str)
    else:
        raise ValueError("Invalid type. Must be 'corpus' or 'idea'.")
    
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()

# use ThreadPoolExecutor to standardize descriptions concurrently
def standardize_concurrently(descriptions: List[str], type: str = "corpus") -> List[str]:
    fn = partial(standardize, type=type)
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(standardize, descriptions))
    return results