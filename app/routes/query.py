from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict
from app.services.retriever import retrieve_top_k

router = APIRouter()

class QueryRequest(BaseModel):
    idea: str
    top_k: int = 5  # optional, default to 5

class MatchMetadata(BaseModel):
    type: str
    score: float
    match_meta: dict  # raw content chunk: description or comment

class ProductMetadata(BaseModel):
    meta: dict  # product name, website, tags, etc.

class CompanyGroup(BaseModel):
    min_score: float
    avg_score: float
    match_percent: float
    product_meta: ProductMetadata
    matches: List[MatchMetadata]

class QueryResponse(BaseModel):
    idea: str
    results: List[CompanyGroup]

@router.post("/query", response_model=QueryResponse)
def query_similar_ideas(request: QueryRequest):
    results, uniqueness = retrieve_top_k(request.idea, top_k=request.top_k)
    return {
        "idea": request.idea,
        "results": results,
    }
