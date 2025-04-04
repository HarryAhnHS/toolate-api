from together import Together
from concurrent.futures import ThreadPoolExecutor
from typing import List, Callable
import os
import time
from tqdm import tqdm
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

# --- Prompt Templates ---
IDEA_PROMPT_TEMPLATE = """
Rewrite the following startup idea into a structured, technical product description.

Startup Idea:
\"\"\"{idea}\"\"\"
"""

CORPUS_DESCRIPTION_PROMPT_TEMPLATE = """
You're an AI assistant helping analyze early-stage AI startups for comparison with other startup ideas in the future. 
Use your existing knowledge and the below product info to rewrite the startup description into a clear, concise, and technical product summary.
Don't use lists or headers. Use clear, natural language in full sentences as if summarizing for an investor or analyst.
Limit the summary to 250 words max.

Focus on:
- What the product does and key pain points it aims to solve
- Target market and key use cases
- Key features or technologies
- Unique value prop if available
- Key drawbacks or limitations

Startup Name: {name}
Startup Tags: {tags}
Startup Created At: {createdAt}

Raw Description:
\"\"\"{description}\"\"\"
"""

CORPUS_COMMENT_PROMPT_TEMPLATE = """
You're analyzing community feedback on a startup.
Rewrite this comment into a clear, sentiment-rich insight about the product, based on both the user tone and your understanding of the product. 
Retain original intent but make it informative. 
Don't use lists or headers. Use clear, natural language in full sentences as if summarizing as a market analyst.

Here is a user or founder comment about the product '{name}'.
User Comment:
\"\"\"{comment}\"\"\"

If vague, try to infer context using product information. Use the product description below to interpret comment meaningfully.
Startup Name: {name}
Tags: {tags}
Created At: {createdAt}
Product Description:
\"\"\"{description}\"\"\"
"""


# --- LLM Wrappers ---

def standardize_idea(idea: str) -> str:
    prompt = IDEA_PROMPT_TEMPLATE.format(idea=idea)
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def build_prompt(entry: dict) -> str:
    match entry["type"]:
        case "description":
            return CORPUS_DESCRIPTION_PROMPT_TEMPLATE.format(
                name=entry["meta"].get("name", ""),
                tags=", ".join(entry["meta"].get("tags", [])),
                createdAt=entry["meta"].get("createdAt", ""),
                description=entry.get("text", "")
            )
        case "comment":
            return CORPUS_COMMENT_PROMPT_TEMPLATE.format(
                name=entry["meta"].get("parent_name", ""),
                tags=", ".join(entry["meta"].get("parent_tags", [])),
                createdAt=entry["meta"].get("parent_createdAt", ""),
                description=entry["meta"].get("parent_description", ""),
                comment=entry.get("text", "")
            )
        case _:
            raise ValueError("Invalid entry type")


def call_llm_with_retry(prompt: str, retries: int = 2, delay: float = 2.0) -> str:
    for attempt in range(retries):
        try:
            time.sleep(1)  # 🧘 1 QPS throttle
            response = client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ Retry {attempt+1}: {e}")
            time.sleep(delay * (2 ** attempt))
    return ""

def standardize_entry(entry: dict, version: str) -> str:
    prompt = build_prompt(entry)
    try:
        standardized = call_llm_with_retry(prompt)
        if standardized:
            entry["standardized"] = standardized
            entry["isEnhanced"] = True
            entry["enhancementVersion"] = version
            entry["enhancedAt"] = datetime.now(timezone.utc).isoformat() 
            return entry
    except Exception as e:
        print(f"❌ Error standardizing entry {entry['id']}: {e}")
    return None

# FOLLOWING IS NOT SUPPORTED BY TOGETHER.AI DUE TO 1 QPS LIMIT - but good to implement for future use
# --- Batched, Threaded Standardization ---
def standardize_batch(entries: List[dict], version: str) -> List[dict]:
    enhanced = []
    for entry in entries:
        result = standardize_entry(entry, version)
        if result:
            enhanced.append(result)
    return enhanced

# multi-threaded standardization - not supported by together.ai due to 1 QPS limit
def standardize_concurrently(
    entries: List[dict],
    batch_size: int = 5,
    max_workers: int = 8,
    on_batch_complete: Callable[[List[dict]], None] = None
) -> List[dict]:
    global current_results
    
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i in range(0, len(entries), batch_size):
            batch = entries[i:i + batch_size]
            futures.append(executor.submit(standardize_batch, batch))

        for future in tqdm(futures):
            try:
                batch_result = future.result()
                results.extend(batch_result)
                current_results.extend(batch_result)

                if on_batch_complete:
                    on_batch_complete(batch_result)
            except Exception as e:
                print(f"❌ Error in batch: {e}")

    return results