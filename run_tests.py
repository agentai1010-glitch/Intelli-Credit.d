from ml_engine.features import extract_features
from ml_engine.model import CreditScoringModel
from ml_engine.explain import explain_prediction
import os

# Sharma Textile Mock Document Data
document_data = {
    "revenue": 42500000,
    "ebitda": 6100000,
    "net_worth": 140000000,
    "existing_debt": 82000000,
    "gst_reconciliation_score": 58,
    "sector_risk": 0
}
# Empty entities that don't increase legal_flag_count
entity_data = []

raw_text = """
Revenue 42500000.
EBITDA 6100000.
Net worth 140000000.
Existing debt 82000000.
"""

# Test 1 - Corrected feature values
print("\n--- TEST 1: Corrected Feature Values ---")
features_df = extract_features(raw_text, document_data, entity_data)
feature_dict = features_df.iloc[0].to_dict()
for k, v in feature_dict.items():
    print(f"  {k}: {v}")

# Delete old mock model to force retrain if it exists
model_path = "model_artifacts/mock_model.txt"
if os.path.exists(model_path):
    os.remove(model_path)

# Test 2 - Feature importance after retraining
print("\n--- TEST 2: Feature Importance after Retraining ---")
model = CreditScoringModel()
model.load_model(model_path) # Forces retrain on new synth data

importance = model.model.feature_importance(importance_type='split')
feature_names = model.model.feature_name()
total_imp = sum(importance)
for name, imp in zip(feature_names, importance):
    pct = (imp / total_imp) * 100 if total_imp > 0 else 0
    print(f"  {name}: {pct:.1f}%")

# Test 3 & 4 & 5 - SHAP values, Final score, Base value
print("\n--- TEST 3, 4, 5: Prediction & SHAP ---")
response = explain_prediction(model, features_df)

print(f"\nTEST 4 - Final Score:")
print(f"  Predicted Score: {response['predicted_score'] * 100} / 100")
print(f"  Decision: {response['decision']}")

print(f"\nTEST 5 - SHAP Base Value:")
print(f"  Base Value: {response.get('base_value')}")

print("\nTEST 3 - SHAP Values (Impacts):")
for feat in response['top_features']:
    direction = "POSITIVE" if feat['impact'] > 0 else "NEGATIVE"
    print(f"  {feat['feature']}: {feat['value']} -> Impact {feat['impact']} ({direction})")
