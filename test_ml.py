# test_ml.py
import json
from ml_engine.features import extract_features
from ml_engine.model import CreditScoringModel
from ml_engine.explain import explain_prediction

def run_test():
    # Mock data mirroring OCR extraction output for Sharma Textile Mills scenario
    raw_text = """Revenue 1000000
Current Assets 600000
Current Liabilities 220000
Total Debt 34000000
Total Equity 58000000"""

    document_data = {
        "revenue": 425000000,                 # 42.5 Cr
        "ebitda": 26000000,                   # 2.6 Cr
        "net_worth": 57800000,                # 5.78 Cr
        "existing_debt": 33900000,            # 3.39 Cr
        "gst_reconciliation_score": 58.0,
        "sector_risk": 0
    }

    # Mock entity extraction with no legal flags
    entity_data = [
        {"type": "ORG", "text": "Sharma Textile Mills Pvt. Ltd."}
    ]

    print("1. Extracting Features...")
    features = extract_features(raw_text, document_data, entity_data)
    print("Features Extracted:\n", features.to_dict(orient="records")[0])

    print("\n2. Initializing & Loading Model...")
    model = CreditScoringModel(reject_threshold=0.6, watchlist_threshold=0.3)
    model.load_model("model_artifacts/lgbm_mock_model.pkl")
    
    print("\n3. Predicting...")
    prediction = model.predict(features)
    print("Prediction Result:\n", json.dumps(prediction, indent=2))

    print("\n4. Explaining Prediction with SHAP...")
    explanation = explain_prediction(model, features)

    # Reformat into requested JSON shape
    shap_values = {}
    for item in explanation.get("top_features", []):
        shap_values[item["feature"]] = item["impact"]

    out = {
        "shap_values": shap_values,
        "feature_values": features.to_dict(orient="records")[0],
        "base_value": None,
        "predicted_value": explanation["predicted_score"]
    }

    print("Explanation JSON:\n", json.dumps(out, indent=2))

if __name__ == "__main__":
    run_test()
