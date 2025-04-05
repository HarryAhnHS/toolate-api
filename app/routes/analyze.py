from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.analyzer import generate_analysis

router = APIRouter()

class MatchMetadata(BaseModel):
    type: str
    score: float
    match_meta: Dict[str, Any]

class ProductMetadata(BaseModel):
    meta: Dict[str, Any]

class CompanyGroup(BaseModel):
    min_score: float
    match_percent: float
    avg_score: float
    product_meta: ProductMetadata
    matches: List[MatchMetadata]

class AnalysisRequest(BaseModel):
    idea: str
    results: List[CompanyGroup]

class AnalysisResponse(BaseModel):
    idea: str
    analysis: Dict[str, str]  # sections: similarities, differences, suggestions, uniqueness_score

@router.post("/analyze", response_model=AnalysisResponse)
def analyze(request: AnalysisRequest):
    analysis = generate_analysis(request.idea, [company.model_dump() for company in request.results])
    return {
        "idea": request.idea,
        "analysis": analysis["analysis"]
    }