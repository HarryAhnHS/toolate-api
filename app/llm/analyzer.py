from typing import List, Dict
from together import Together
import os
import json
import re

from app.core.config import LLM_MODEL_NAME

client = Together(api_key=os.getenv("QUERY_LLM_API_KEY"))

ANALYSIS_PROMPT_TEMPLATE = """
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

1. **Similarities**  
   Look for recurring patterns in product tags, summaries, or features across all retrieved products. Summarize what *shared elements* the user's idea seems to align with.

2. **Differences**  
   Note how the user's idea stands apart in terms of features, audience, technology, or scope — especially if there are large L2 distances or missing themes.

3. **Suggestions**  
   Recommend smart ways the idea could be improved, better positioned, or focused to carve a niche. Use user comments as insight into *what's missing or requested* in the market.

4. **Uniqueness Score**  
   Based on average L2 distance, match_percent, and product similarities, estimate a uniqueness score from 0 to 100:
   - `0 = nearly identical to existing products`
   - `100 = completely original with no overlap`

---

## Output Format
Respond as if you are a consultant for the user, and directly address them as "you" or "your".
Return your analysis as a JSON object with the following structure:

{{
  "similarities": "Your analysis of shared themes and patterns (in markdown format)",
  "differences": "Your analysis of how the idea stands apart (in markdown format)", 
  "suggestions": "Your recommendations for improvement (in markdown format)",
  "uniqueness_score": "A single number from 0 to 100 (as a string)"
}}

IMPORTANT: 
- Return ONLY the JSON object, no additional text before or after
- Do NOT wrap the JSON in markdown code blocks (```)
- Ensure all string values are properly escaped for JSON (escape quotes with \", newlines with \n, etc.)
- If your content contains markdown formatting, keep it but ensure it's properly JSON-escaped
- Return raw, valid JSON only
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

def fix_json_string(content: str) -> str:
    """Fix common JSON string issues like unescaped quotes and newlines."""
    # Escape backslashes first (but not already escaped ones)
    content = re.sub(r'\\(?!["\\/bfnrt])', r'\\\\', content)
    
    # Escape unescaped quotes
    content = re.sub(r'(?<!\\)"', r'\\"', content)
    
    # Convert actual newlines to \n
    content = content.replace('\n', '\\n').replace('\r', '\\r')
    
    # Convert tabs to \t
    content = content.replace('\t', '\\t')
    
    return content

def parse_json_response(json_str: str) -> Dict[str, str]:
    """Parse JSON response from LLM, with fallback handling for malformed JSON."""
    import re
    
    # Clean the input string
    cleaned = json_str.strip()
    
    # Remove markdown code blocks if present
    if cleaned.startswith('```') and cleaned.endswith('```'):
        # Remove opening ```json or ``` and closing ```
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned)
        cleaned = cleaned.strip()
    
    try:
        # Try to parse the cleaned JSON directly
        parsed = json.loads(cleaned)
        
        # Ensure all required keys are present with default values
        result = {
            "similarities": parsed.get("similarities", ""),
            "differences": parsed.get("differences", ""),
            "suggestions": parsed.get("suggestions", ""),
            "uniqueness_score": str(parsed.get("uniqueness_score", "0"))
        }
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parsing failed: {e}")
        print(f"⚠️ Raw content first 500 chars: {json_str[:500]}")
        
        # Try to manually extract and fix the JSON structure
        try:
            # Look for the basic structure and extract field contents
            # This handles the case where LLM returns unescaped newlines in JSON values
            
            result = {
                "similarities": "",
                "differences": "",
                "suggestions": "",
                "uniqueness_score": "0"
            }
            
            # Pattern to match each field - handles multiline content
            fields_pattern = r'"(similarities|differences|suggestions|uniqueness_score)":\s*"(.*?)"(?=\s*[,}])'
            
            # For multiline matching, we need to be more careful
            # Split the content to find each field manually
            for field_name in ["similarities", "differences", "suggestions", "uniqueness_score"]:
                # Find the start of this field
                field_start_pattern = f'"{field_name}":\\s*"'
                match = re.search(field_start_pattern, json_str)
                
                if match:
                    # Start after the opening quote
                    start_pos = match.end()
                    
                    # Find the end by looking for the closing quote followed by comma or }
                    # but ignore escaped quotes
                    pos = start_pos
                    content = ""
                    while pos < len(json_str):
                        char = json_str[pos]
                        if char == '"' and (pos == start_pos or json_str[pos-1] != '\\'):
                            # Found unescaped quote - check if it's the end
                            next_pos = pos + 1
                            while next_pos < len(json_str) and json_str[next_pos].isspace():
                                next_pos += 1
                            if next_pos < len(json_str) and json_str[next_pos] in ',}':
                                # This is the end quote
                                break
                        content += char
                        pos += 1
                    
                    result[field_name] = content
            
            return result
            
        except Exception as manual_error:
            print(f"⚠️ Manual parsing also failed: {manual_error}")
            # Final fallback: return empty structure
            return {
                "similarities": "Error parsing response",
                "differences": "Error parsing response", 
                "suggestions": "Error parsing response",
                "uniqueness_score": "0"
            }

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

    parsed = parse_json_response(raw_output)

    return {
        "idea": idea,
        "analysis": parsed
    }