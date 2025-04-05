from typing import List, Dict
from together import Together
import os

from app.core.config import LLM_MODEL_NAME

client = Together(api_key=os.getenv("QUERY_LLM_API_KEY"))

ANALYSIS_PROMPT_TEMPLATE =ANALYSIS_PROMPT_TEMPLATE = """
You are an expert analyst for AI startup ideas.

A user submitted the following startup idea:
\"\"\"{idea}\"\"\"

Your task is to analyze the idea based on the {n} similar products retrieved via semantic search. Each product includes:
- L2 similarity scores (lower = more similar)
- Product tags (representing industry, niche, or feature set)
- Standardized summaries of descriptions and/or user comments

{company_blocks}

---

## What to do:

1. **Compare Themes**  
   Look for recurring patterns in product tags, summaries, or features across all retrieved products. Summarize what *shared elements* the user’s idea seems to align with.

2. **Identify Distinctions**  
   Note how the user’s idea stands apart in terms of features, audience, technology, or scope — especially if there are large L2 distances or missing themes.

3. **Suggest Improvements**  
   Recommend smart ways the idea could be improved, better positioned, or focused to carve a niche. Use user comments as insight into *what’s missing or requested* in the market.

4. **Score Uniqueness**  
   Based on average L2 distance, match_percent, and product similarities, estimate a uniqueness score:
   - `0 = nearly identical to existing products`
   - `100 = completely original with no overlap`
   Just return a number — no explanation.

---

## Output Format (Markdown only)

Respond with the following **Markdown sections only**:

**Similarities**

**Differences**

**Suggestions**

**Uniqueness Score**
"""


def format_company_block(company: Dict, index: int) -> str:
    product_meta = company["product_meta"]
    product_name = product_meta["meta"]["name"]
    product_tags = ", ".join(product_meta["meta"]["tags"])
    website = product_meta["meta"]["website"]
    min_score = company["min_score"]
    avg_score = company["avg_score"]
    match_percent = company["match_percent"]

    block = f"### {index}. {product_name} ({website})\n"
    block += f"- Tags: {product_tags}\n"
    block += f"- Closest L2 distance: {min_score:.4f}\n"
    block += f"- Avg L2 distance: {avg_score:.4f}\n"
    block += f"- Match percent: {match_percent:.2f}\n"
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
        "**Similarities**": "similarities",
        "**Differences**": "differences",
        "**Suggestions**": "suggestions",
        "**Uniqueness Score**": "uniqueness_score"
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