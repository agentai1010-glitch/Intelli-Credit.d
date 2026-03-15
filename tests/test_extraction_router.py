import json
from unittest.mock import patch
from ml_engine.features import extract_features
from ocr_pipeline.ocr_utils import extract_document

FIXTURES = {
    "ANNUAL_REPORT": "tests/fixtures/sarvam_annual_report_output.json",
    "BANK_STATEMENT": "tests/fixtures/sarvam_bank_statement_output.json",
    "GST_RETURN": "tests/fixtures/sarvam_gstr3b_output.json",
    "GSTR2A": "tests/fixtures/sarvam_gstr2a_output.json",
    "SANCTION_LETTER": "tests/fixtures/sarvam_sanction_letter_output.json"
}

def mock_extract(pdf_path, doc_type_for_fixture=None):
    # Determine doc_type from path if not provided
    dt = doc_type_for_fixture
    if not dt:
        for k in FIXTURES.keys():
            if k in pdf_path:
                dt = k
                break
    
    with open(FIXTURES[dt], "r", encoding="utf-8") as f:
        return json.load(f)

def run_pipeline_test():
    with patch("ocr_pipeline.sarvam_client.extract_with_sarvam", side_effect=lambda p: mock_extract(p)), \
         patch("ocr_pipeline.ocr_utils.run_ocr_with_tesseract") as mock_tess:
        
        document_data = {}
        for doc_type in FIXTURES.keys():
            parsed_doc = extract_document(f"mock_{doc_type}.pdf", doc_type)
            document_data.update(parsed_doc)
            
        print("\n--- Document Data Extraction Complete ---")
        print(f"Pytesseract fallbacks triggered: {mock_tess.call_count}")

        # Map 'debt' key from annual report to 'total_debt' which ml_engine/features.py 
        # normally expects (since it looks for 'total_debt' or 'existing_debt').
        if "debt" in document_data:
            document_data["total_debt"] = document_data.pop("debt")
            
        # Manually providing the implicit GST reconciliation score since there is no live API
        # doing the cross-document GST match in the test script. 
        # (GST 100 - 20 - 7 - 15 = 58)
        document_data["gst_reconciliation_score"] = 58.0
        
        # Manually providing standard sector risk 0 for testing purposes
        document_data["sector_risk"] = 0
            
        # Running features file natively
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

if __name__ == "__main__":
    run_pipeline_test()
