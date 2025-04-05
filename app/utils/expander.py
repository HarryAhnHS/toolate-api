from together import Together
from typing import List
import os
from dotenv import load_dotenv
import json

from app.core.config import LLM_MODEL_NAME

load_dotenv()

client = Together(api_key=os.getenv("QUERY_TOGETHER_API_KEY"))
# --- Prompt Templates ---
QUERY_EXPANSION_PROMPT_TEMPLATE = """
Expand the following startup idea into {n_expansions} semantically diverse paraphrases. 
Each paraphrase should use alternate terminology **within the same functional and domain boundaries**
Do not change the domain or scope. The startup idea must remain in the same industry and solve the same class of problem.
Avoid introducing generic or unrelated terms that might dilute the original specificity.

For each paraphrase, use natural language in full sentences. 
Each paraphrase should be ≤100 words. 
If the original idea is short, keep it concise; if it's long, rephrase with the same level of depth but stay within the word limit.

Return the output as a JSON list of {n_expansions} strings. Example:

[
  "First paraphrase here.",
  "Another phrasing of the startup idea...",
  "...",
  "Final paraphrase here."
]

Startup Idea:
\"\"\"{idea}\"\"\"
"""

# Query Expansion - user query -> list of semantically diverse paraphrases
def expand_query(idea: str, n_expansions: int = 3) -> List[str]:
    prompt = QUERY_EXPANSION_PROMPT_TEMPLATE.format(idea=idea, n_expansions=n_expansions)
    response = client.chat.completions.create(
        model=LLM_MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )
    return json.loads(response.choices[0].message.content.strip()) #returns list of n_expansions strings