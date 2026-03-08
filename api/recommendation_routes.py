from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from ml_engine.loan_pricing_engine import compute_loan_limit, compute_interest_rate, generate_sanction_terms

router = APIRouter()

class QualitativeDelta(BaseModel):
    pending_litigation: Optional[bool] = False
    management_quality: Optional[str] = "AVERAGE"
    industry_outlook: Optional[str] = "STABLE"
    collateral_quality: Optional[str] = "STANDARD"

class RecommendationRequest(BaseModel):
    risk_score: int
    revenue: float
    debt: float
    ebitda: float
    collateral_value: float
    gst_reconciliation_score: float
    qualitative_delta: QualitativeDelta

class StepDetail(BaseModel):
    step: str
    value: float
    reason: str

class SanctionTerms(BaseModel):
    decision: str
    facility_type: str
    tenure_months: int
    conditions_precedent: List[str]
    covenants: List[str]

class RecommendationResponse(BaseModel):
    recommended_limit_cr: float
    limit_calculation_steps: List[StepDetail]
    recommended_rate_pct: float
    rate_calculation_steps: List[StepDetail]
    sanction_terms: SanctionTerms

@router.post("/terms", response_model=RecommendationResponse)
async def get_recommendation_terms(payload: RecommendationRequest):
    try:
        limit_info = compute_loan_limit(
            risk_score=payload.risk_score,
            revenue=payload.revenue,
            debt=payload.debt,
            ebitda=payload.ebitda,
            collateral_value=payload.collateral_value,
            gst_reconciliation_score=payload.gst_reconciliation_score
        )
        
        rate_info = compute_interest_rate(
            risk_score=payload.risk_score,
            qualitative_delta=payload.qualitative_delta.model_dump()
        )
        
        terms = generate_sanction_terms(
            limit=limit_info["recommended_limit_cr"],
            rate=rate_info["recommended_rate_pct"],
            risk_score=payload.risk_score
        )
        
        # Override decision mapped natively
        if rate_info["recommended_rate_pct"] >= 16.0 and limit_info["recommended_limit_cr"] == 0:
            terms["decision"] = "REJECT"

        return RecommendationResponse(
            recommended_limit_cr=limit_info["recommended_limit_cr"],
            limit_calculation_steps=limit_info["limit_calculation_steps"],
            recommended_rate_pct=rate_info["recommended_rate_pct"],
            rate_calculation_steps=rate_info["rate_calculation_steps"],
            sanction_terms=terms
        )
    except Exception as e:
        print(f"Error in recommendation terms: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate recommendation terms.")

from ml_engine.counterfactual import compute_counterfactuals

class CounterfactualRequest(BaseModel):
    features: Dict[str, float]
    risk_score: float
    shap_values: Dict[str, float]

class CounterfactualItem(BaseModel):
    factor: str
    current_value: float
    target_value: float
    score_improvement: float
    new_projected_score: float
    action: str

class CounterfactualResponse(BaseModel):
    counterfactuals: List[CounterfactualItem]

@router.post("/counterfactual", response_model=CounterfactualResponse)
async def get_counterfactuals(payload: CounterfactualRequest):
    try:
        f = dict(payload.features)
        
        # Hydrate ratio features if missing from raw inputs
        if "revenue_expense_ratio" not in f and f.get("revenue", 0) > 0:
            f["revenue_expense_ratio"] = f.get("ebitda", 0) / f.get("revenue", 1)
            
        if "working_capital" not in f:
            f["working_capital"] = f.get("net_worth", 0) - f.get("existing_debt", 0)
            
        if "debt_equity_ratio" not in f and f.get("net_worth", 0) > 0:
            f["debt_equity_ratio"] = f.get("existing_debt", 0) / f.get("net_worth", 1)

        res = compute_counterfactuals(f, payload.risk_score, payload.shap_values)
        return {"counterfactuals": res}
    except Exception as e:
        print(f"Error in counterfactuals: {e}")
        raise HTTPException(status_code=500, detail="Failed to compute counterfactuals.")
