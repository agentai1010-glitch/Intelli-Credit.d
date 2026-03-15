"""
Explainability module using SHAP.
Wrapped defensively so a SHAP failure never crashes the score endpoint.
"""

import shap
import numpy as np
import pandas as pd
from typing import Dict, Any
from ml_engine.model import MODEL_FEATURES


def explain_prediction(model_instance, features: pd.DataFrame) -> Dict[str, Any]:
    """
    Returns top SHAP features and their impact scores.
    Uses shap.TreeExplainer designed for LightGBM models.
    Slices to MODEL_FEATURES before SHAP so column count always matches.
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
        # Use the same Model-feature slice that predict() uses
        model_input = features.reindex(columns=MODEL_FEATURES, fill_value=0).astype(float)

        explainer = shap.TreeExplainer(booster)
        shap_values = explainer.shap_values(model_input)

        if isinstance(explainer.expected_value, (list, np.ndarray)):
            base_value = float(
                explainer.expected_value[1]
                if isinstance(shap_values, list)
                else explainer.expected_value[0]
            )
        else:
            base_value = float(explainer.expected_value)

        # For regression: shap_values is 2D [samples x features]
        # For multiclass: it's a list — use positive class
        val_arr = shap_values[1][0] if isinstance(shap_values, list) else shap_values[0]

        feature_names = model_input.columns.tolist()
        feature_values = model_input.iloc[0].values

        impacts = []
        for i, val in enumerate(val_arr):
            feat_val = float(feature_values[i])
            if np.isnan(feat_val):
                feat_val = None
            else:
                feat_val = round(feat_val, 4)
                
            imp_val = float(val)
            if np.isnan(imp_val):
                imp_val = 0.0
            else:
                imp_val = round(imp_val, 6)
                
            impacts.append({
                "feature": feature_names[i],
                "value": feat_val,
                "impact": imp_val
            })

        # Sort by absolute magnitude descending
        impacts.sort(key=lambda x: abs(x["impact"]), reverse=True)
        print(f"[explain] Top 3 SHAP impacts: {impacts[:3]}")

    except Exception as e:
        print(f"[explain] SHAP computation failed: {e}")
        impacts = []
        base_value = None

    return {
        "predicted_score": prediction_info["predicted_score"],
        "decision": prediction_info["decision"],
        "top_features": impacts,
        "base_value": base_value
    }
