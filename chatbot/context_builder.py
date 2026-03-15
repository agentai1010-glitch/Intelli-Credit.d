"""
Context Builder — constructs a rich structured credit context dict for the chatbot.
Takes the full session data available after CAM generation.
"""
from typing import Any, Dict


def build_credit_context(session_data: dict) -> dict:
    """
    Build a rich credit context dict from session/pipeline data.

    Parameters
    ----------
    session_data : Full session dict (from AppContext or post-CAM pipeline state).
                  Accepts both frontend camelCase and backend snake_case keys.

    Returns
    -------
    Fully structured context dict for the chatbot system prompt.
    """
    features = session_data.get("features") or session_data.get("extractedFinancials") or {}
    score_result = session_data.get("scoreResult") or session_data.get("score_result") or {}
    pricing = session_data.get("loan_pricing_engine") or session_data.get("loanPricing") or {}
    analyst = session_data.get("analystInputs") or session_data.get("analyst_inputs") or {}
    gst = session_data.get("gst_reconciliation") or {}

    # ── Company basics ───────────────────────────────────────────────────────
    company_name = (
        session_data.get("company_name")
        or session_data.get("companyName")
        or features.get("company_name")
        or "Unknown Company"
    )
    sector = (
        features.get("sector_name")
        or session_data.get("sector_name")
        or "Textile Manufacturing"
    )

    # ── Score waterfall ──────────────────────────────────────────────────────
    base_ml_score = int(session_data.get("baseScore") or session_data.get("base_score") or 91)
    qualitative_delta = int(session_data.get("qualitativeDelta") or session_data.get("qualitative_delta") or -19)
    regulatory_score = int(session_data.get("regulatoryScore") or session_data.get("regulatory_score") or 85)
    final_score = int(session_data.get("finalScore") or session_data.get("final_score") or 72)
    recon_score = int(session_data.get("reconciliationScore") or gst.get("reconciliation_score") or 58)

    # GST penalty: score drop from 100-point GST scale to the base score
    # Formula: gst_impact = -1 * int(round((100 - recon_score) * 0.18))
    gst_penalty = -1 * int(round((100 - recon_score) * 0.18))

    # Regulatory impact
    reg_impact = 0
    if regulatory_score < 60:
        reg_impact = -20
    elif regulatory_score < 80:
        reg_impact = -5

    decision = session_data.get("decision") or ("APPROVE" if final_score >= 70 else "WATCHLIST" if final_score >= 50 else "REJECT")

    # ── Loan terms ───────────────────────────────────────────────────────────
    loan_limit_raw = session_data.get("loanLimit") or session_data.get("loan_limit") or pricing.get("recommended_limit_cr") or 7.65
    if isinstance(loan_limit_raw, str):
        import re
        # Match a number that starts with a digit (skips the Rs. prefix)
        m = re.search(r'\d+\.?\d*', loan_limit_raw.replace(",", ""))
        loan_limit_cr = float(m.group()) if m else 7.65
    else:
        loan_limit_cr = float(loan_limit_raw)

    interest_rate = float(pricing.get("recommended_rate_pct") or session_data.get("interestRatePct") or 10.0)
    tenure_months = int(pricing.get("tenure_months") or session_data.get("tenureMonths") or 12)

    # ── ML Features ──────────────────────────────────────────────────────────
    wc = features.get("working_capital") or 58000000
    der = features.get("debt_equity_ratio") or 0.5857
    rer = features.get("revenue_expense_ratio") or 0.1435
    gst_match = features.get("gst_bank_match_score") or 0.58
    legal = int(features.get("legal_flag_count") or 0)
    sector_risk = int(features.get("sector_risk_flag") or 0)

    def cr(val): return f"Rs.{val/10000000:.2f}Cr"

    ml_features = {
        "working_capital": {
            "value": cr(wc),
            "signal": "GREEN",
            "meaning": "positive liquidity buffer"
        },
        "debt_equity_ratio": {
            "value": f"{der:.3f}x",
            "signal": "GREEN" if der < 1.0 else "RED",
            "meaning": "healthy leverage below 1.0" if der < 1.0 else "high leverage"
        },
        "revenue_expense_ratio": {
            "value": f"{rer:.3f}",
            "signal": "GREEN" if rer > 0.10 else "AMBER",
            "meaning": f"{rer*100:.1f}% EBITDA margin, improving"
        },
        "gst_bank_match_score": {
            "value": f"{gst_match:.2f}",
            "signal": "RED" if gst_match < 0.70 else "GREEN",
            "meaning": "fraud risk detected" if gst_match < 0.70 else "clean GST compliance"
        },
        "legal_flag_count": {
            "value": str(legal),
            "signal": "GREEN" if legal == 0 else "RED",
            "meaning": "no legal issues" if legal == 0 else f"{legal} legal flags detected"
        },
        "sector_risk_flag": {
            "value": str(sector_risk),
            "signal": "GREEN" if sector_risk == 0 else "RED",
            "meaning": "textile is medium risk sector" if sector_risk == 0 else "elevated sector risk"
        }
    }

    # ── GST flags (use provided or defaults with full detail) ─────────────
    raw_flags = session_data.get("gstFlags") or gst.get("flags") or []
    if raw_flags and isinstance(raw_flags[0], dict):
        gst_flags = raw_flags  # already structured
    else:
        # Build rich structured flags from flat list or defaults
        flag_detail_map = {
            "CIRCULAR_TRADING_RISK": {
                "severity": "HIGH",
                "penalty_pts": -20,
                "detail": "ITC claimed Rs.58L vs available Rs.42L — 38.1% gap exceeds 20% threshold"
            },
            "REVENUE_MISMATCH": {
                "severity": "MEDIUM",
                "penalty_pts": -7,
                "detail": "GST turnover Rs.3.85Cr vs bank credits Rs.3.55Cr — 8.45% gap"
            },
            "SUSPICIOUS_TRANSACTIONS": {
                "severity": "HIGH",
                "penalty_pts": -15,
                "detail": "3x round Rs.50L transactions on Jun-12, Jul-11, Sep-04"
            }
        }
        flag_list = (
            raw_flags if isinstance(raw_flags, list) and raw_flags
            else ["CIRCULAR_TRADING_RISK", "REVENUE_MISMATCH", "SUSPICIOUS_TRANSACTIONS"]
        )
        gst_flags = []
        for f in flag_list:
            key = f if isinstance(f, str) else f.get("flag", "UNKNOWN")
            detail = flag_detail_map.get(key, {"severity": "MEDIUM", "penalty_pts": 0, "detail": key})
            gst_flags.append({"flag": key, **detail})

    total_gst_penalty = sum(f.get("penalty_pts", 0) for f in gst_flags)
    gst_formula = f"100 {' '.join([str(f['penalty_pts']) for f in gst_flags])} = {recon_score}/100"

    # ── Qualitative adjustments ───────────────────────────────────────────
    raw_qual = session_data.get("qualitativeAdjustments") or session_data.get("qualitative_adjustments") or []
    if not raw_qual:
        # Reconstruct from analyst inputs + known delta
        qual_adjustments = []
        mgmt = analyst.get("management_quality", "AVERAGE")
        mgmt_impact = -5 if mgmt == "AVERAGE" else (5 if mgmt == "GOOD" else -10)
        qual_adjustments.append({"factor": "Management Quality", "rating": mgmt.title(), "impact": mgmt_impact})

        outlook = analyst.get("industry_outlook", "STABLE")
        out_impact = 6 if outlook == "FAVORABLE" else (0 if outlook == "STABLE" else -5)
        qual_adjustments.append({"factor": "Industry Outlook", "rating": outlook.title(), "impact": out_impact})

        lit = analyst.get("pending_litigation", True)
        lit_impact = -18 if lit else 0
        qual_adjustments.append({"factor": "Pending Litigation", "rating": "Yes" if lit else "No", "impact": lit_impact})

        cap = analyst.get("capacity_utilization", 55)
        qual_adjustments.append({"factor": "Capacity Utilization", "rating": f"{cap}%", "impact": 0})
    else:
        qual_adjustments = raw_qual

    # ── Enrichment from PageIndex ─────────────────────────────────────────
    auditor = features.get("auditor_qualification") or session_data.get("auditor_qualification") or "Unqualified"
    rev_trend = (
        features.get("revenue_trend")
        or session_data.get("revenue_trend")
        or "FY2023: Rs.35.0Cr -> FY2024: Rs.38.0Cr -> FY2025: Rs.42.5Cr (21.4% growth over 2 years)"
    )

    # ── Counterfactual improvement paths ──────────────────────────────────
    improvement_paths = (
        session_data.get("improvement_paths")
        or [
            {"action": "Resolve pending litigation", "score_gain": "+18 pts",
             "detail": "Litigation flag carries -18pt qualitative penalty"},
            {"action": f"Improve GST compliance score from {gst_match:.2f} to 0.75+",
             "score_gain": "+7 to +9 pts",
             "detail": "ITC gap reduction from 38.1% to below 20% threshold required"},
            {"action": f"Reduce debt-equity ratio from {der:.3f}x to below 0.470x",
             "score_gain": "+5.8 pts",
             "detail": "Achieved by retiring ~Rs.1.5Cr in short-term borrowings"}
        ]
    )

    return {
        # Company basics
        "company_name": company_name,
        "sector": sector,
        "gstin": session_data.get("gstin", "24AABCS1234F1Z3"),

        # Score waterfall
        "base_ml_score": base_ml_score,
        "gst_penalty": gst_penalty,
        "qualitative_penalty": qualitative_delta,
        "regulatory_impact": reg_impact,
        "final_score": final_score,
        "decision": decision,

        # Loan terms
        "loan_limit_cr": loan_limit_cr,
        "interest_rate": interest_rate,
        "tenure_months": tenure_months,

        # 6 ML features with labels
        "ml_features": ml_features,

        # GST
        "gst_flags": gst_flags,
        "gst_reconciliation_score": recon_score,
        "gst_formula": gst_formula,

        # Qualitative
        "qualitative_adjustments": qual_adjustments,

        # PageIndex enrichment
        "auditor_qualification": auditor.capitalize() if auditor else "Unqualified",
        "revenue_trend": rev_trend,

        # Improvements
        "improvement_paths": improvement_paths
    }
