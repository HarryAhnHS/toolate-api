from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict
from app.services.analyzer import generate_analysis

router = APIRouter()

class MatchMetadata(BaseModel):
    type: str
    score: float
    match_meta: dict  # contains standardized text, tags, etc.

class ProductMetadata(BaseModel):
    meta: dict  # contains name, website, etc.

class CompanyGroup(BaseModel):
    min_score: float
    product_meta: ProductMetadata
    matches: List[MatchMetadata]

class AnalysisRequest(BaseModel):
    idea: str
    results: List[CompanyGroup]

@router.post("/analyze")
def analyze(request: AnalysisRequest):
    analysis = generate_analysis(request.idea, [company.dict() for company in request.results])
    return {
        "idea": request.idea,
        "analysis": analysis
    }