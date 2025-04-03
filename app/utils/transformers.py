import os
from dotenv import load_dotenv
from transformers import AutoTokenizer

load_dotenv()

# Use the same tokenizer as your model to count tokens properly
st_model = os.getenv("ST_MODEL")  
tokenizer = AutoTokenizer.from_pretrained(st_model)

def needs_truncation(text: str, max_tokens: int = 512) -> bool:
    return len(tokenizer.encode(text, truncation=False)) > max_tokens

def needs_enrichment(text: str, min_tokens: int = 10) -> bool:
    return len(tokenizer.encode(text, truncation=False)) < min_tokens