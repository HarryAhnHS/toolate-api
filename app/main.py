from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class IdeaRequest(BaseModel):
    input: str

@app.post("/eval")
def evaluate_idea(data: IdeaRequest):
    # Placeholder response
    return {
        "score": 83,
        "similar_startups": ["Stripe", "Plaid", "Unit"],
        "feedback": "Your idea overlaps with existing fintech tools...",
        "pivot_suggestion": "Consider focusing on API security for banks."
    }