from together import Together
# from concurrent.futures import ThreadPoolExecutor
from typing import List

import os
from dotenv import load_dotenv

load_dotenv()

# Standardize the description/input prior to embedding

client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

PROMPT_TEMPLATE = """
Summarize this startup idea into a clear 3-4 sentence product description.
Focus on what the product does, its core functionality, and who it's for.

Idea:
\"\"\"{idea}\"\"\"
"""

def standardize(raw_desc: str) -> str:
    prompt = PROMPT_TEMPLATE.format(idea=raw_desc)
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()

# use ThreadPoolExecutor to standardize descriptions concurrently
# def standardize_concurrently(descriptions: List[str]) -> List[str]:
#     with ThreadPoolExecutor(max_workers=10) as executor:
#         results = list(executor.map(standardize, descriptions))
#     return results