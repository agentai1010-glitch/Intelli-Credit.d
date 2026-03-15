import sys
sys.path.insert(0, '.')
from ml_engine.model import CreditScoringModel
from ml_engine.features import extract_features
from ml_engine.explain import explain_prediction

m = CreditScoringModel()
m.load_model('model_artifacts/mock_model.txt')

doc = {
    'revenue': 425000000,
    'ebitda': 61000000,
    'net_worth': 140000000,
    'existing_debt': 82000000,
    'working_capital': 58000000,
    'gst_reconciliation_score': 58,
    'debt_equity_ratio': 0.586,
    'sector_risk': 0,
}

f = extract_features('', doc, [])
print("Feature DataFrame:")
print(f[['revenue_expense_ratio','working_capital','debt_equity_ratio','gst_bank_match_score','legal_flag_count','sector_risk_flag']].to_string())

res = m.predict(f)
print("\nPredict result:", res)

exp = explain_prediction(m, f)
print("\nTop SHAP features:")
for feat in exp['top_features']:
    print(f"  {feat['feature']:30s}  value={feat['value']:.4f}  impact={feat['impact']:+.6f}")
