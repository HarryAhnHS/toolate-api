from app.llm.analyzer import generate_analysis as llm_generate_analysis
from typing import List, Dict

def generate_analysis(idea: str, results: List[Dict]) -> Dict:
    return llm_generate_analysis(idea, results)