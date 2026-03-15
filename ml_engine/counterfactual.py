def compute_counterfactuals(features: dict, risk_score: float, shap_values: dict) -> list:
    """
    Simulates improvements in the top factors that are DRAGGING DOWN the credit score.
    In our model, a POSITIVE SHAP value increases risk (decreases credit score).
    """
    # Find factors that increase risk (v > 0) and sort by descending impact
    sorted_drags = sorted([(k, v) for k, v in shap_values.items() if v > 0], key=lambda x: x[1], reverse=True)
    top_3 = sorted_drags[:3]
    
    results = []
    for factor, shap_val in top_3:
        curr_val = features.get(factor, 0.0)
        
        # Approximate score improvement: Reducing a risk drag by 50%
        # This is high-level simulation for the UI
        score_imp = abs(shap_val) * 0.50 * 100 
        new_score = min(99, risk_score + score_imp)
        
        factor_lower = factor.lower()
        if "debt" in factor_lower or "ratio" in factor_lower or "flag" in factor_lower:
            # For risk ratios or counts, reduce them
            target_val = curr_val * 0.7
            action = f"Improve {factor.replace('_', ' ')} by 30%"
        elif "match" in factor_lower or "score" in factor_lower:
            # For match scores, increase them
            target_val = min(1.0, curr_val * 1.5)
            action = f"Improve {factor.replace('_', ' ')} logic/data"
        else:
            target_val = curr_val * 1.2
            action = f"Optimize {factor.replace('_', ' ')}"
            
        results.append({
            "factor": factor,
            "current_value": round(float(curr_val), 2),
            "target_value": round(float(target_val), 2),
            "score_improvement": round(float(score_imp), 1),
            "new_projected_score": round(float(new_score), 1),
            "action": action
        })
        
    # Model-relevant fallbacks
    default_suggestions = [
        {
            "factor": "gst_bank_match_score",
            "current_value": features.get("gst_bank_match_score", 0.5),
            "target_value": 0.95,
            "score_improvement": 8.5,
            "new_projected_score": risk_score + 8.5,
            "action": "Resolve GST reconciliation gaps"
        },
        {
            "factor": "legal_flag_count",
            "current_value": features.get("legal_flag_count", 1.0),
            "target_value": 0.0,
            "score_improvement": 12.0,
            "new_projected_score": risk_score + 12.0,
            "action": "Clear pending legal or adverse findings"
        },
        {
            "factor": "debt_equity_ratio",
            "current_value": features.get("debt_equity_ratio", 1.5),
            "target_value": 1.0,
            "score_improvement": 5.2,
            "new_projected_score": risk_score + 5.2,
            "action": "Reduce leverage via capital infusion"
        }
    ]

    if len(results) < 3:
        existing_factors = {r["factor"] for r in results}
        for item in default_suggestions:
            if item["factor"] not in existing_factors:
                item["new_projected_score"] = min(99, risk_score + item["score_improvement"])
                results.append(item)
                existing_factors.add(item["factor"])
            if len(results) >= 3:
                break
        
    return results

if __name__ == "__main__":
    import json
    features = {"debt_equity_ratio": 2.8, "current_ratio": 1.1, "capacity_utilization": 40}
    risk_score = 72
    shap_values = {"debt_equity_ratio": -0.18, "current_ratio": -0.12, "capacity_utilization": -0.09}
    
    res = compute_counterfactuals(features, risk_score, shap_values)
    print(json.dumps(res, indent=2))
