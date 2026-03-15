import json
from ml_engine.pageindex_extractor import extract_with_pageindex
from ml_engine.features import merge_extraction_sources

def main():
    with open("tests/fixtures/pageindex_doc_id.txt", "r") as f:
        doc_id = f.read().strip()
        
    print(f"Running extract_with_pageindex('{doc_id}') ...\n")
    pageindex_data = extract_with_pageindex(doc_id)
    
    with open("tests/fixtures/sarvam_annual_report_output.json", "r") as f:
        sarvam_raw = json.load(f)
        
    from ml_engine.smart_parser import parse_with_sarvam
    sarvam_data = parse_with_sarvam(sarvam_raw, "ANNUAL_REPORT")
        
    print("\nFIELD                    SARVAM VALUE        PAGEINDEX VALUE     MATCH?")
    print("─────────────────────────────────────────────────────────────────────────")
    
    fields = [
        "revenue", "ebitda", "net_worth", "existing_debt", 
        "contingent_liabilities", "related_party_exposure", 
        "auditor_qualification", "off_balance_sheet_items", 
        "revenue_trend", "sector"
    ]
    
    for field in fields:
        sarvam_key = "debt" if field == "existing_debt" else field
        s_val = sarvam_data.get(sarvam_key, None)
        if s_val is None:
             s_val_str = "None (not found)"
        else:
             s_val_str = str(s_val)

        p_val = pageindex_data.get(field, None)
        p_val_str = str(p_val) if p_val is not None else "None"
        
        match_str = ""
        if s_val is None and p_val is not None:
             match_str = "NEW FIND"
        elif s_val is None and p_val is None:
             match_str = "N/A"
        elif s_val is not None and p_val is not None:
             try:
                 diff = abs(float(s_val) - float(p_val)) / max(float(s_val), 1e-9)
                 if diff <= 0.05:
                     match_str = "YES"
                 else:
                     match_str = "NO: MISMATCH"
             except Exception:
                 match_str = "?"
        else:
             match_str = "?"
             
        print(f"{field:<24} {s_val_str:<19} {p_val_str:<19} {match_str}")

    print("\n\n--- TASK 3: merge_extraction_sources ---")
    merged = merge_extraction_sources(sarvam_data, pageindex_data)

if __name__ == "__main__":
    main()
