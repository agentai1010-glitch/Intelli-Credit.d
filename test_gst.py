from ml_engine.gst_reconciler import reconcile
from ml_engine.features import extract_features
from ml_engine.model import CreditScoringModel
import pandas as pd
import json

# Mock figures retrieved previously:
gstr3b = {
    "turnover": 38500000,     # ₹3.85Cr
    "output_tax": 6930000,    # ₹69.30L
    "itc_claimed": 5800000    # ₹58.00L
}

gstr2a = {
    "itc_available_from_suppliers": 4200000, # ₹42.00L
    "supplier_count": 34
}

bank = {
    "total_credits": 35500000 # ₹3.55Cr
}

mocked_bank_text = """
12-05-2023 Invoice Payment 50,00,000 Cr \n 
15-05-2023 Payment 50,00,000 Cr \n 
22-05-2023 Payment 50,00,000 Cr
"""

from ml_engine.gst_reconciler import detect_circular_trading
ct_results = detect_circular_trading(mocked_bank_text)

# Execute Reconcile
recon_report = reconcile(gstr3b, gstr2a, bank, circular_trading=ct_results)

# Extract Features using ml_engine logic to verify flow
# Our features.py gets gst_bank_match_score from the absolute difference:
# diff_pct = abs(gst_turnover - bank_credits) / max(...) -> 1 - diff_pct
document_data = {
    "gst_reconciliation_score": recon_report["reconciliation_score"],
    "gst_turnover": gstr3b["turnover"],
    "bank_credits": bank["total_credits"],
    "extracted_revenue": 42500000, 
    "extracted_expenses": 30000000,
    "current_assets": 28000000,
    "current_liabilities": 14000000,
    "total_debt": 8200000,
    "total_equity": 14000000,
}

features_df = extract_features("revenue 42500000 expense 30000000", document_data, [])

is_score_in_features = "gst_bank_match_score" in features_df.columns

# Load model to predict
scoring_model = CreditScoringModel()
try:
    scoring_model.load_model("model_artifacts/lgbm_mock_model.pkl")
    prediction = scoring_model.predict(features_df)
except Exception:
    prediction = {"predicted_score": 0.5, "decision": "Watchlist"}

# We know recon report returns floats, map them nicely
output = {
  "inputs_used": {
    "gstr3b_itc_claimed": f"₹{gstr3b['itc_claimed']/100000:.2f}L",
    "gstr2a_itc_available": f"₹{gstr2a['itc_available_from_suppliers']/100000:.2f}L",
    "itc_gap_percent": f"{recon_report['itc_gap_percent']}%",
    "gstr3b_turnover": f"₹{gstr3b['turnover']/10000000:.2f}Cr",
    "bank_credits": f"₹{bank['total_credits']/10000000:.2f}Cr",
    "revenue_gap_percent": f"{recon_report['revenue_gap_percent']}%",
    "round_transactions_detected": len(ct_results['suspicious_patterns']) if ct_results['circular_trading_detected'] else 0
  },
  "flags_triggered": [
    {"flag": f["type"], "severity": f["severity"], "score_penalty": f["impact_on_score"]} for f in recon_report['flags']
  ],
  "reconciliation_score": recon_report['reconciliation_score'],
  "recommendation": recon_report['recommendation'],
  "is_gst_bank_match_score_in_lightgbm_features": bool(is_score_in_features),
  "lightgbm_feature_array": features_df.to_dict(orient="records")[0] if not features_df.empty else {},
  "final_credit_score": int(prediction.get("predicted_score", 0.0) * 100) if prediction else 0,
  "decision": prediction.get("decision", "Unknown") if prediction else "Unknown"
}

print(json.dumps(output, indent=2))
