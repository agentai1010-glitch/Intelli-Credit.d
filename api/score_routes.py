"""
FastAPI routes for model scoring and SHAP explanations.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from nlp_module.ner_extractor import extract_entities
from ml_engine.features import extract_features
from ml_engine.model import CreditScoringModel
from ml_engine.explain import explain_prediction

router = APIRouter()

# ── Load model ONCE at startup ──
scoring_model = CreditScoringModel()
try:
    scoring_model.load_model("model_artifacts/lgbm_mock_model.pkl")
    print("[score_routes] LightGBM model loaded successfully.")
except Exception as e:
    print(f"[score_routes] WARNING: Model load failed: {e}. Scoring will fall back to defaults.")


@router.post("/score/")
async def score_company(parsed_data: Dict[str, Any]):
    """
    Accepts raw text or document data, extracts NLP entities, engineers features,
    and returns a credit score with SHAP explainability.
    """
    document_data = parsed_data.get("document_data", {})
    raw_text = parsed_data.get("raw_text", "")

    # 1. Extract NLP Entities (fault-tolerant)
    try:
        entities = extract_entities(raw_text)
    except Exception as e:
        print(f"[score_routes] NER extraction failed: {e}")
        entities = []

    # 2. Feature Engineering (fault-tolerant)
    try:
        features_df = extract_features(raw_text, document_data, entities)
    except Exception as e:
        print(f"[score_routes] Feature extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Feature extraction failed: {str(e)}")

    # 3. Score (fault-tolerant)
    try:
        prediction = scoring_model.predict(features_df)
    except Exception as e:
        print(f"[score_routes] Model prediction failed: {e}")
        # Return a safe default score if model is broken
        prediction = {"predicted_score": 0.5, "decision": "Watchlist"}

    # 4. SHAP Explainability (fault-tolerant — non-critical, don't crash if it fails)
    try:
        explanation = explain_prediction(scoring_model, features_df)
    except Exception as e:
        print(f"[score_routes] SHAP explanation failed (non-critical): {e}")
        explanation = {
            "predicted_score": prediction.get("predicted_score", 0.5),
            "decision": prediction.get("decision", "Watchlist"),
            "top_features": []
        }

    return {
        "status": "success",
        "nlp_entities": entities,
        "score_result": prediction,
        "explanation": explanation
    }
