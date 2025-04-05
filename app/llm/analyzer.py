from typing import List, Dict
from together import Together
import os

from app.core.config import LLM_MODEL_NAME

client = Together(api_key=os.getenv("QUERY_LLM_API_KEY"))

ANALYSIS_PROMPT_TEMPLATE = """
You are an AI startup analyst.
A user submitted this startup idea:
\"\"\"{idea}\"\"\"

Below are {n} similar products retrieved via semantic search. 
Each includes a standardized summary and optionally product comments / descriptions.

{company_blocks}

Your task (depending on the vagueness/specificity of the user's idea):
1. Analyze and summarize what common themes or features exist between the user's idea and these products.
2. Explain how the user’s idea is different or uniquely positioned.
3. Suggest improvements, pivots, or differentiation strategies the user could explore.
4. Offer a numerical score between 0 and 100 for how unique the user's idea is compared to the retrieved products.

Within each section, feel free to use any markdown formatting that you see fit.
For uniqueness score, respond a single number between 0 and 100, where 0 is the most similar and 100 is the most unique.
Respond in markdown format with the following sections and nothing else. 

**Similarities**

**Differences**

**Suggestions**

**Uniqueness Score**
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
        summary = match_meta.get("standardized", "[No summary]")

        if match_type == "description":
            block += f"- 🧾 Description L2 distance (score: {score:.4f}):\n  {summary}\n\n"
        elif match_type == "comment":
            block += f"- 💬 Comment L2 distance (score: {score:.4f}):\n  {summary}\n\n"

    return block.strip()

def parse_markdown_sections(markdown: str) -> Dict[str, str]:
    sections = {
        "similarities": "",
        "differences": "",
        "suggestions": "",
        "uniqueness_score": ""
    }

    current_key = None
    buffer = []

    section_headers = {
        "**similarities**": "similarities",
        "**differences**": "differences",
        "**suggestions**": "suggestions",
        "**uniqueness score**": "uniqueness_score"
    }

    for line in markdown.splitlines():
        line = line.strip()
        lower_line = line.lower()

        if lower_line in section_headers:
            if current_key:
                sections[current_key] = "\n".join(buffer).strip()
            current_key = section_headers[lower_line]
            buffer = []
        elif current_key:
            buffer.append(line)

    if current_key and buffer:
        sections[current_key] = "\n".join(buffer).strip()

    return sections

def generate_analysis(idea: str, results: List[Dict], model_name=LLM_MODEL_NAME) -> Dict:
    if not results:
        return {
            "idea": idea,
            "analysis": {
                "similarities": "",
                "differences": "",
                "suggestions": "",
                "uniqueness_score": ""
            }
        }

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

    raw_output = response.choices[0].message.content.strip()
    print("🧾 Raw model output:\n", raw_output)

    parsed = parse_markdown_sections(raw_output)

    return {
        "idea": idea,
        "analysis": parsed
    }