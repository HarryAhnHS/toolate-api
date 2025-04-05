from typing import List, Dict
from together import Together
import os

from app.core.config import TOGETHER_MODEL_NAME

client = Together(api_key=os.getenv("QUERY_TOGETHER_API_KEY"))

ANALYSIS_PROMPT_TEMPLATE = """
You are an AI startup analyst.

A user submitted this startup idea:
\"\"\"{idea}\"\"\"

Below are {n} similar products retrieved via semantic search. 
Each includes a standardized summary and optionally a product comment.

{company_blocks}

Your task:
1. Analyze and summarize what common themes or features exist between the user's idea and these products.
2. Explain how the user’s idea is different or uniquely positioned.
3. Suggest improvements, pivots, or differentiation strategies the user could explore.

Respond in **Markdown format**, under the sections:
- **Similarities**
- **Differences**
- **Suggestions**
"""

def format_company_block(company: Dict, index: int) -> str:
    product_meta = company["product_meta"]
    product_name = product_meta["meta"]["name"]
    website = product_meta["meta"]["website"]
    min_score = company["min_score"]

    block = f"### {index}. {product_name} ({website})\n"
    block += f"- Closest L2 distance: {min_score:.4f}\n"

    for match in company["matches"]:
        match_type = match["type"]
        score = match["score"]
        match_meta = match["match_meta"]

        if match_type == "description":
            summary = match_meta.get("standardized", "[No summary]")
            block += f"- 🧾 Description match (score: {score:.4f}):\n  {summary}\n\n"

        elif match_type == "comment":
            summary = match_meta.get("standardized", "[No comment content]")
            block += f"- 💬 Comment match (score: {score:.4f}):\n  {summary}\n\n"

    return block.strip()

def generate_analysis(idea: str, results: List[Dict], model_name=TOGETHER_MODEL_NAME) -> str:
    if not results:
        return "No similar companies found to analyze. Please try a different query."

    company_blocks = "\n\n".join(format_company_block(company, i + 1) for i, company in enumerate(results))

    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        idea=idea.strip(),
        n=len(results),
        company_blocks=company_blocks
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1200
    )

    return response.choices[0].message.content.strip()