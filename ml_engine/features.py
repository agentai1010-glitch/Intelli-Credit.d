import pandas as pd
import re
from typing import Dict, List

def merge_extraction_sources(sarvam_data: dict, pageindex_data: dict) -> dict:
    """
    Merge core fields from Sarvam and deep fields from PageIndex.
    Scale-aware merge: If PageIndex differs by 10x, it likely has correct denomination.
    """
    merged_data = sarvam_data.copy()
    
    # We trust PageIndex's denomination detection more for core numeric fields
    CORE_NUMERIC_FIELDS = ["revenue", "ebitda", "net_worth", "existing_debt"]
    
    for field in CORE_NUMERIC_FIELDS:
        v_sarvam = sarvam_data.get(field)
        if field == "existing_debt" and v_sarvam is None:
            v_sarvam = sarvam_data.get("debt")
            
        v_pageindex = pageindex_data.get(field)

        if v_sarvam and v_pageindex:
            try:
                s_val = float(v_sarvam)
                p_val = float(v_pageindex)
                
                if s_val == 0 or p_val == 0:
                    merged_data[field] = v_sarvam or v_pageindex
                    continue

                ratio = max(s_val, p_val) / min(s_val, p_val)

                if ratio > 8: # A bit more than 10x to catch slightly varying large numbers
                    # Scale error — PageIndex has denomination context, trust it
                    print(f"[SCALE_ERROR] {field} — {round(ratio)}x diff, using PageIndex")
                    merged_data[field] = v_pageindex
                elif ratio > 1.05:
                    # Normal mismatch — Sarvam direct table read wins
                    print(f"[MISMATCH] {field} — using Sarvam")
                    merged_data[field] = v_sarvam
                else:
                    print(f"[MERGE] {field} matches within tolerance. Using Sarvam.")
                    merged_data[field] = v_sarvam
            except Exception as e:
                print(f"[MERGE_ERROR] {field}: {e}")
                merged_data[field] = v_sarvam
        elif v_sarvam is not None:
            merged_data[field] = v_sarvam
        elif v_pageindex is not None:
            merged_data[field] = v_pageindex
            
    deep_fields = ["contingent_liabilities", "related_party_exposure", "auditor_qualification", "off_balance_sheet_items", "revenue_trend", "sector"]
    for field in deep_fields:
        v_pageindex = pageindex_data.get(field)
        if v_pageindex not in [None, "None", ""]:
            merged_data[field] = v_pageindex
            print(f"[MERGE] {field} from PageIndex.")
        # If PageIndex is None, we KEEP the sarvam_data value already in merged_data
            
    return merged_data

def extract_features(raw_text: str, document_data: Dict, entity_data: List[Dict]) -> pd.DataFrame:
    """
    Ingests cleaned raw_text from OCR and applies regex extraction for real financial figures.
    Computes basic financial ratios and other features.
    """
    feature_dict = {
        "working_capital": 0.0,
        "debt_equity_ratio": 0.0,
        "gst_bank_match_score": 0.0,
        "legal_flag_count": 0,
        "sector_risk_flag": 0
    }
    
    # New feature definitions per user request
    text = str(raw_text).replace(',', '').lower()
    
    revenue = float(document_data.get("extracted_revenue", document_data.get("revenue", 0)) or 0)
    ebitda = float(document_data.get("extracted_expenses", document_data.get("ebitda", 0)) or 0)
    
    feature_dict["revenue_expense_ratio"] = 0.0
    if revenue and revenue > 0 and ebitda is not None:
        try:
            feature_dict["revenue_expense_ratio"] = float(ebitda) / float(revenue)
        except:
            pass
        
    net_worth_match = re.search(r'net worth[^\d]*(\d+)', text)
    net_worth = float(net_worth_match.group(1)) if net_worth_match else document_data.get("net_worth", 0)
    
    debt_match = re.search(r'existing debt[^\d]*(\d+)', text)
    existing_debt = float(debt_match.group(1)) if debt_match else document_data.get("existing_debt", document_data.get("total_debt", document_data.get("debt", 0)))
    
    nw_val = float(net_worth or 0)
    dt_val = float(existing_debt or 0)
    feature_dict["working_capital"] = nw_val - dt_val
    
    if nw_val > 0:
        feature_dict["debt_equity_ratio"] = dt_val / nw_val
    elif "debt_equity_ratio" in document_data:
        try:
            feature_dict["debt_equity_ratio"] = float(document_data.get("debt_equity_ratio", 0))
        except:
            feature_dict["debt_equity_ratio"] = 0.0
        
    # GST vs Bank vs ITC match score (1.0 = perfect match, 0.0 = terrible match)
    # The reconciler already gives us a 0-100 score, map it directly!
    reconciliation_score = document_data.get("reconciliation_score", document_data.get("gst_reconciliation_score"))
    if reconciliation_score is not None:
        feature_dict["gst_bank_match_score"] = float(reconciliation_score) / 100.0
    else:
        # Fallback multi-signal ratio if no pre-computed recon score provided
        v_gst = document_data.get("gst_turnover", document_data.get("turnover", 0))
        gst_turnover = float(v_gst or 0)
        v_bank = document_data.get("bank_credits", document_data.get("total_credits", 0))
        bank_credits = float(v_bank or 0)
        itc_claimed = document_data.get("itc_claimed")
        itc_available = document_data.get("itc_available")
        
        t_match = 1.0
        if max(gst_turnover, bank_credits) > 0:
            t_match = 1.0 - (abs(gst_turnover - bank_credits) / max(gst_turnover, bank_credits))
            
        i_match = 1.0
        if itc_claimed is not None and itc_available is not None:
             ic = float(itc_claimed)
             ia = float(itc_available)
             if max(ic, ia) > 0:
                 i_gap = abs(ic - ia) / max(ic, ia)
                 i_match = max(0.0, 1.0 - (i_gap * 1.5)) # Penalize ITC 1.5x
        
        # Multiplicative strictly penalized approach
        final_match = t_match * i_match
        if t_match < 0.9 or i_match < 0.8:
            final_match *= 0.9
            
        feature_dict["gst_bank_match_score"] = max(0.0, min(1.0, final_match))

    # Number of red flags from entities (e.g., LAW type entities, NPA mentions)
    red_flag_count = 0
    for ent in entity_data:
        if ent.get("type") in ["LAW"]:
            red_flag_count += 1
        text_check = ent.get("text", "").lower()
        if "npa" in text_check or "insolvency" in text_check or "default" in text_check:
            red_flag_count += 1
            
    # Use provided legal_flag_count if available (e.g. from regulatory news), 
    # otherwise fallback to NLP-derived count from OCR text.
    feature_dict["legal_flag_count"] = document_data.get("legal_flag_count", red_flag_count)
    
    # Sector risk flag (Example: 1 for high risk, 0 for normal)
    feature_dict["sector_risk_flag"] = document_data.get("sector_risk", 0)
    
    # Enrichment fields from PageIndex (passed via document_data)
    feature_dict["auditor_qualification"] = str(document_data.get("auditor_qualification", "") or "")
    feature_dict["revenue_trend"] = str(document_data.get("revenue_trend", "") or "")
    feature_dict["sector_name"] = str(document_data.get("sector", "") or "")
    
    aud_qual = str(document_data.get("auditor_qualification", "")).lower()
    if "unqualified" in aud_qual:
        feature_dict["auditor_risk_flag"] = 0
    elif "qualified" in aud_qual:
        feature_dict["auditor_risk_flag"] = 1
    else:
        feature_dict["auditor_risk_flag"] = 0
    
    # --- Final Scaling Guard ---
    # Ensure all currency-denominated features are absolute rupees 
    # to match the model training expectations (e.g. division by 100M)
    for k in ["revenue", "ebitda", "net_worth", "existing_debt", "working_capital"]:
        if k in feature_dict:
            val = feature_dict[k]
            # If value is < 1000, it's almost certainly in Crores (from Sarvam/PageIndex)
            # 1000 Cr is 10 Billion, which is a safe upper bound for single value scaling check
            if 0 < val < 1000:
                feature_dict[k] = val * 10_000_000
                
    # Recompute ratios if scaled
    if feature_dict.get("revenue", 0) > 0:
        feature_dict["revenue_expense_ratio"] = float(feature_dict.get("ebitda", 0)) / float(feature_dict["revenue"])
    if feature_dict.get("net_worth", 0) > 0:
        feature_dict["debt_equity_ratio"] = float(feature_dict.get("existing_debt", 0)) / float(feature_dict["net_worth"])
        
    return pd.DataFrame([feature_dict])
