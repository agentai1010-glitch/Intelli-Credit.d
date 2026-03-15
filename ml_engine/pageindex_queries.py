ANNUAL_REPORT_QUERIES = {
    # Core financials — use broad year terms so it works for any FY
    "revenue": (
        "What is the total Revenue from Operations for the most recent financial year "
        "(e.g. FY2024, FY2023, or the latest year available) in this Annual Report? "
        "Return ONLY the numeric value in Crores (e.g. '8,200.00 Cr' or '8200 Crore'). "
        "Do NOT return a table. If not found, say 'None'."
    ),
    "ebitda": (
        "What is the EBITDA or Operating Profit (Profit before Interest, Depreciation, and Tax) "
        "for the most recent financial year in this Annual Report? "
        "Return ONLY the numeric value in Crores. If EBITDA is not directly stated, "
        "calculate it as: Revenue - Operating Expenses (excluding interest and depreciation). "
        "If not found, say 'None'."
    ),
    "net_worth": (
        "What is the total Net Worth or Shareholders' Equity (including Equity Share Capital + "
        "Reserves and Surplus) as of the latest Balance Sheet date in this Annual Report? "
        "Return ONLY the numeric value in Crores. If not found, say 'None'."
    ),
    "net_profit": (
        "What is the Net Profit After Tax (PAT) for the most recent financial year in this Annual Report? "
        "Return ONLY the numeric value in Crores. If not found, say 'None'."
    ),
    "existing_debt": (
        "What is the total Debt (Long-term Borrowings + Short-term Borrowings) as of the latest "
        "Balance Sheet date in this Annual Report? "
        "Return ONLY the numeric value in Crores. If not found, say 'None'."
    ),
    "auditor_qualification": (
        "What opinion did the statutory auditor give on the financial statements in this Annual Report? "
        "Was it an Unqualified/Clean opinion, or a Qualified opinion? "
        "Return ONLY: 'Unqualified' or 'Qualified'. If not clear, say 'Unqualified'."
    ),
    "sector": (
        "Based on the company name, business description, and operations described in this Annual Report, "
        "what industry or sector does this company operate in? "
        "Return ONLY the sector name (e.g. 'Media & Entertainment', 'Textiles', 'IT Services'). "
        "If not clear, say 'Diversified'."
    ),
}
