"""
Explainability module using SHAP.
Wrapped defensively so a SHAP failure never crashes the score endpoint.
"""

import shap
import pandas as pd
from typing import Dict, Any


def explain_prediction(model_instance, features: pd.DataFrame) -> Dict[str, Any]:
    """
    Returns top SHAP features and their impact scores.
    Uses shap.TreeExplainer designed for LightGBM models.
    Returns empty top_features list if SHAP fails (non-critical path).
    """
    prediction_info = model_instance.predict(features)

    booster = model_instance.model
    if booster is None:
        return {
            "predicted_score": prediction_info["predicted_score"],
            "decision": prediction_info["decision"],
            "top_features": []
        }

    try:
        explainer = shap.TreeExplainer(booster)
        shap_values = explainer.shap_values(features)

        # For regression: shap_values is 2D [samples x features]
        # For multiclass: it's a list — use positive class
        if isinstance(shap_values, list):
            val_arr = shap_values[1][0]
        else:
            val_arr = shap_values[0]

        feature_names = features.columns.tolist()
        feature_values = features.iloc[0].values

        impacts = []
        for i, val in enumerate(val_arr):
            impacts.append({
                "feature": feature_names[i],
                "value": round(float(feature_values[i]), 2),
                "impact": round(float(val), 4)
            })

        # Sort by absolute magnitude, return top 5
        impacts.sort(key=lambda x: abs(x["impact"]), reverse=True)
        top_features = impacts[:5]

    except Exception as e:
        print(f"[explain] SHAP computation failed: {e}")
        top_features = []

    return {
        "predicted_score": prediction_info["predicted_score"],
        "decision": prediction_info["decision"],
        "top_features": top_features
    }
