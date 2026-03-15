import json
import pandas as pd
from unittest.mock import patch
from ml_engine.features import extract_features
from ocr_pipeline.ocr_utils import extract_document
from ml_engine.model import CreditScoringModel

FIXTURES = {
    "ANNUAL_REPORT": "tests/fixtures/sarvam_annual_report_output.json",
    "BANK_STATEMENT": "tests/fixtures/sarvam_bank_statement_output.json",
    "GST_RETURN": "tests/fixtures/sarvam_gstr3b_output.json",
    "GSTR2A": "tests/fixtures/sarvam_gstr2a_output.json",
    "SANCTION_LETTER": "tests/fixtures/sarvam_sanction_letter_output.json"
}

def mock_extract(pdf_path, doc_type_for_fixture=None):
    dt = doc_type_for_fixture
    if not dt:
        for k in FIXTURES.keys():
            if k in pdf_path:
                dt = k
                break
    with open(FIXTURES[dt], "r", encoding="utf-8") as f:
        return json.load(f)

def mock_pageindex_extract(doc_id):
    return {
        'revenue': 425000000.0,
        'ebitda': 61000000.0,
        'net_worth': 140000000.0,
        'existing_debt': 82000000.0,
        'contingent_liabilities': None,
        'related_party_exposure': None,
        'auditor_qualification': 'unqualified',
        'off_balance_sheet_items': None,
        'revenue_trend': 'FY2023: 35.0 Cr\nFY2024: 38.0 Cr\nFY2025: 42.5 Cr',
        'sector': 'Textiles'
    }

def run_pipeline_test():
    with patch("ocr_pipeline.sarvam_client.extract_with_sarvam", side_effect=lambda p: mock_extract(p)), \
         patch("ml_engine.pageindex_extractor.extract_with_pageindex", side_effect=mock_pageindex_extract), \
         patch("ocr_pipeline.ocr_utils.run_ocr_with_tesseract") as mock_tess:
        
        document_data = {}
        for doc_type in FIXTURES.keys():
            parsed_doc = extract_document(f"mock_{doc_type}.pdf", doc_type)
            document_data.update(parsed_doc)
            
        print("\n--- Document Data Extraction Complete ---")
        
        if "debt" in document_data:
            document_data["total_debt"] = document_data.pop("debt")
            
        document_data["gst_reconciliation_score"] = 58.0
        document_data["sector_risk"] = 0
            
        print("\n--- Running ml_engine.features.extract_features ---")
        features_df = extract_features("", document_data, entity_data=[])
        
        features_dict = features_df.to_dict(orient="records")[0]
        print("\n--- Final Computed Features ---")
        print(f"working_capital = {features_dict['working_capital']}")
        print(f"revenue_expense_ratio = {features_dict['revenue_expense_ratio']}")
        print(f"debt_equity_ratio = {features_dict['debt_equity_ratio']}")
        print(f"gst_bank_match_score = {features_dict['gst_bank_match_score']}")
        print(f"legal_flag_count = {features_dict['legal_flag_count']}")
        print(f"sector_risk_flag = {features_dict['sector_risk_flag']}")
        
        print(f"\n--- Enrichment Fields ---")
        print(f"auditor_qualification = {features_dict.get('auditor_qualification')!r}")
        print(f"revenue_trend = {features_dict.get('revenue_trend')!r}")
        print(f"sector_name = {features_dict.get('sector_name')!r}")
        print(f"auditor_risk_flag = {features_dict.get('auditor_risk_flag')}")
        
        print("\n--- LightGBM Scoring ---")
        # Extract only the 6 LightGBM-compatible columns (exclude enrichment + metadata columns)
        LGBM_COLS = ["revenue_expense_ratio", "working_capital", "debt_equity_ratio",
                     "gst_bank_match_score", "legal_flag_count", "sector_risk_flag"]
        lgbm_df = features_df[LGBM_COLS]
        
        scoring_model = CreditScoringModel()
        scoring_model.load_model("model_artifacts/mock_model.txt")
        result = scoring_model.predict(lgbm_df)
        
        credit_score = int(result["predicted_score"] * 100)
        decision = result["decision"]
        
        # Loan limit calculation (from cam_routes pricing engine logic)
        net_worth_val = features_dict.get("working_capital", 0) + features_dict.get("existing_debt", document_data.get("total_debt", 0))
        revenue_val = document_data.get("revenue", 0)
        ebitda_val = document_data.get("ebitda", 0)
        loan_limit = min(revenue_val * 0.18, ebitda_val * 1.25)
        if loan_limit == 0:
            loan_limit = 7650000.0
        rate = 10.0
        
        print(f"LightGBM score = {credit_score}, Decision = {decision}, Limit = Rs.{loan_limit/1e7:.2f}Cr, Rate = {rate}%")

if __name__ == "__main__":
    run_pipeline_test()
