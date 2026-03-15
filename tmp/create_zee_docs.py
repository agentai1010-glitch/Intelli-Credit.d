"""
Generate 5 realistic mock documents for Zee Entertainment Enterprises Ltd.
Saved to mock_documents/zee/
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable)
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
except ImportError:
    print("Installing reportlab...")
    os.system("pip install reportlab")
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable)
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'mock_documents', 'zee')
os.makedirs(OUT_DIR, exist_ok=True)

styles = getSampleStyleSheet()
H1 = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=16, spaceAfter=6,
                     textColor=colors.HexColor('#1a1a2e'), alignment=TA_CENTER)
H2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=13, spaceAfter=4,
                     textColor=colors.HexColor('#16213e'))
BODY = ParagraphStyle('BODY', parent=styles['Normal'], fontSize=10, spaceAfter=4,
                       leading=15)
WARN = ParagraphStyle('WARN', parent=styles['Normal'], fontSize=10, spaceAfter=4,
                       leading=15, textColor=colors.HexColor('#c0392b'))
BOLD = ParagraphStyle('BOLD', parent=styles['Normal'], fontSize=10, spaceAfter=4,
                       leading=15, fontName='Helvetica-Bold')
SMALL = ParagraphStyle('SMALL', parent=styles['Normal'], fontSize=8, spaceAfter=2,
                        textColor=colors.grey)

def tbl(data, col_widths=None, header_row=True):
    t = Table(data, colWidths=col_widths)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0 if header_row else -1),
         colors.HexColor('#2c3e50') if header_row else colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white if header_row else colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f9f9f9'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cccccc')),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]
    t.setStyle(TableStyle(style))
    return t

def hr():
    return HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#aaaaaa'),
                      spaceAfter=8, spaceBefore=8)

# ─────────────────────────────────────────────────────────────────────────────
# 1. ANNUAL REPORT
# ─────────────────────────────────────────────────────────────────────────────
def doc1():
    path = os.path.join(OUT_DIR, 'mock_zee_annual_report.pdf')
    doc = SimpleDocTemplate(path, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []
    story.append(Paragraph("ZEE ENTERTAINMENT ENTERPRISES LTD.", H1))
    story.append(Paragraph("Annual Report — FY 2023-24", H1))
    story.append(Paragraph("CIN: L92132MH1982PLC028524 | GSTIN: 27AAACZ0503R1ZS", SMALL))
    story.append(Paragraph("Sector: Media &amp; Entertainment | Exchange: BSE/NSE", SMALL))
    story.append(Spacer(1, 10))
    story.append(hr())

    story.append(Paragraph("1. Company Overview", H2))
    story.append(Paragraph(
        "Zee Entertainment Enterprises Ltd. (ZEEL) is one of India's largest media and "
        "entertainment companies, operating a diverse portfolio of television channels, "
        "digital content platforms, and international broadcasting networks. "
        "The company operates across 173+ countries with content in 18 languages. "
        "FY2024 has been marked by significant operational stress following the collapse "
        "of the Sony merger and ongoing NCLT proceedings.", BODY))
    story.append(Spacer(1, 8))

    story.append(Paragraph("2. Financial Summary — FY 2023-24 (Consolidated)", H2))
    fin_data = [
        ['Particulars', 'FY 2023-24 (Rs. Cr)', 'FY 2022-23 (Rs. Cr)', 'YoY Change'],
        ['Total Revenue from Operations', '8,200.00', '8,645.20', '-5.2%'],
        ['Other Income', '182.50', '210.30', '-13.2%'],
        ['Total Income', '8,382.50', '8,855.50', '-5.3%'],
        ['Content Cost & Programming', '4,920.00', '4,870.00', '+1.0%'],
        ['Employee Benefits Expense', '680.00', '640.00', '+6.3%'],
        ['Marketing & Distribution', '520.00', '490.00', '+6.1%'],
        ['Other Operating Expenses', '442.50', '805.50', '-45.1%'],
        ['Total Expenses', '6,562.50', '6,805.50', '-3.6%'],
        ['EBITDA', '820.00', '1,050.00', '-21.9%'],
        ['EBITDA Margin (%)', '10.0%', '12.1%', '-2.1pp'],
        ['Depreciation & Amortisation', '310.00', '290.00', '+6.9%'],
        ['EBIT', '510.00', '760.00', '-32.9%'],
        ['Finance Costs', '285.00', '210.00', '+35.7%'],
        ['Exceptional Items (Loss)', '-405.00', '-120.00', ''],
        ['Profit / (Loss) Before Tax', '-180.00', '430.00', ''],
        ['Tax Expense / (Credit)', '48.00', '118.00', ''],
        ['PAT (Net Profit / Loss)', '-228.00', '312.00', ''],
    ]
    story.append(tbl(fin_data, col_widths=[8*cm, 3.5*cm, 3.5*cm, 2.5*cm]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("3. Balance Sheet Highlights — FY 2023-24", H2))
    bs_data = [
        ['Balance Sheet Item', 'Amount (Rs. Cr)'],
        ['Equity Share Capital', '96.00'],
        ['Other Equity / Reserves', '4,004.00'],
        ['Total Net Worth (Equity)', '4,100.00'],
        ['Long Term Borrowings', '1,950.00'],
        ['Short Term Borrowings / CC', '680.00'],
        ['Total Debt', '2,630.00'],
        ['Debt-to-Equity Ratio', '0.64x'],
        ['Trade Payables', '1,240.00'],
        ['Total Liabilities', '6,850.00'],
        ['Fixed Assets (Net Block)', '1,920.00'],
        ['Intangible Assets (Content)', '2,100.00'],
        ['Trade Receivables', '1,480.00'],
        ['Cash & Bank Balances', '142.00'],
        ['Total Assets', '6,850.00'],
        ['Working Capital', '-380.00'],
        ['Current Ratio', '0.78x'],
    ]
    story.append(tbl(bs_data, col_widths=[10*cm, 5.5*cm]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("4. Key Financial Ratios", H2))
    ratio_data = [
        ['Ratio', 'FY 2023-24', 'FY 2022-23', 'Benchmark'],
        ['DSCR (Debt Service Coverage)', '0.82x', '2.10x', '>1.25x'],
        ['Net Profit Margin', '-2.8%', '3.6%', '>5%'],
        ['EBITDA Margin', '10.0%', '12.1%', '>15%'],
        ['Return on Equity (ROE)', '-5.6%', '7.6%', '>10%'],
        ['Return on Capital Employed', '3.2%', '8.9%', '>12%'],
        ['Interest Coverage Ratio', '1.79x', '3.62x', '>3.0x'],
        ['Debt-to-Equity', '0.64x', '0.42x', '<0.5x'],
    ]
    story.append(tbl(ratio_data, col_widths=[7*cm, 3*cm, 3*cm, 3*cm]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("5. Notes to Accounts — Selected Disclosures", H2))
    story.append(Paragraph("<b>Note 31 — Legal and Regulatory Proceedings:</b>", BODY))
    story.append(Paragraph(
        "The Company is subject to ongoing NCLT proceedings initiated by certain creditors "
        "and former joint venture partners. The National Company Law Tribunal (NCLT), Mumbai "
        "Bench, has admitted petitions under Section 241 and 242 of the Companies Act, 2013. "
        "The Company is vigorously contesting these proceedings. The financial impact, if any, "
        "on the Company's financial position cannot be reasonably estimated at this stage. "
        "Management has obtained legal opinion that the Company has strong grounds for defense.", WARN))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Note 38 — Promoter Pledge Status:</b>", BODY))
    story.append(Paragraph(
        "As of 31st March 2024, promoter group entities have pledged approximately 67.8% of "
        "their shareholding (representing 18.4% of total paid-up equity capital) as security "
        "for various financial obligations. This represents a significant increase from 51.2% "
        "pledging reported in FY2023.", WARN))
    story.append(Spacer(1, 6))

    story.append(Paragraph("6. Auditor's Report — Key Matters", H2))
    story.append(Paragraph("<b>Basis for Qualified Opinion:</b>", BOLD))
    story.append(Paragraph(
        "Qualified opinion — material uncertainty related to going concern. "
        "The Company has reported a net loss of Rs. 228 Crores for the year ended "
        "31st March 2024. Current liabilities exceed current assets by Rs. 380 Crores. "
        "The Company's ability to continue as a going concern is dependent upon successful "
        "resolution of NCLT proceedings, refinancing of borrowings due within 12 months "
        "(Rs. 820 Crores), and improvement in operating cash flows. These conditions indicate "
        "a material uncertainty that may cast significant doubt on the Company's ability to "
        "continue as a going concern.", WARN))
    story.append(Paragraph(
        "Auditor: Walker Chandiok &amp; Co LLP (Grant Thornton) | Registration: 001076N/N500013", SMALL))

    doc.build(story)
    print(f"Created: {path}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. BANK STATEMENT
# ─────────────────────────────────────────────────────────────────────────────
def doc2():
    path = os.path.join(OUT_DIR, 'mock_zee_bank_statement.pdf')
    doc = SimpleDocTemplate(path, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []
    story.append(Paragraph("HDFC BANK LIMITED", H1))
    story.append(Paragraph("Current Account Statement — FY 2023-24", H1))
    story.append(Spacer(1, 6))
    info = [
        ['Account Holder:', 'Zee Entertainment Enterprises Ltd.'],
        ['Account Number:', 'XXXX XXXX 4821 (Masked)'],
        ['Account Type:', 'Current Account (Corporate)'],
        ['Branch:', 'BKC, Mumbai — IFSC: HDFC0000128'],
        ['Statement Period:', '01-Apr-2023 to 31-Mar-2024'],
        ['GSTIN of Customer:', '27AAACZ0503R1ZS'],
    ]
    story.append(tbl(info, col_widths=[5*cm, 11.5*cm], header_row=False))
    story.append(Spacer(1, 12))
    story.append(hr())

    story.append(Paragraph("Account Summary", H2))
    summary = [
        ['Particulars', 'Amount (Rs. Cr)'],
        ['Opening Balance (01-Apr-2023)', '48.50'],
        ['Total Credits (Inflows)', '420.00'],
        ['Total Debits (Outflows)', '445.00'],
        ['Net Movement', '-25.00'],
        ['Closing Balance (31-Mar-2024)', '-8.50  (OVERDRAFT)'],
    ]
    story.append(tbl(summary, col_widths=[10*cm, 6.5*cm]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Transaction Detail — FY 2023-24 (Selected)", H2))
    txn_data = [
        ['Date', 'Description', 'Credit (Cr)', 'Debit (Cr)', 'Balance (Cr)'],
        ['05-Apr-2023', 'NEFT — Sony Pictures — Content License', '85.00', '', '133.50'],
        ['12-Apr-2023', 'RTGS — Essel Group Entities', '', '50.00', '83.50'],
        ['18-Apr-2023', 'Star India Pvt Ltd — Distribution Rights', '62.00', '', '145.50'],
        ['22-Apr-2023', 'Vendor Payment — Content Production', '', '38.20', '107.30'],
        ['30-Apr-2023', 'Salary & Wages — Apr 2023', '', '52.40', '54.90'],
        ['14-May-2023', 'HDFC Bank — CC Interest Recovery', '', '12.50', '42.40'],
        ['28-May-2023', 'RTGS — Round Transfer — Essel Finance', '', '50.00', '-7.60'],
        ['02-Jun-2023', 'Subscriber Revenue — ZEE5 Digital', '40.00', '', '32.40'],
        ['15-Jun-2023', 'Salary & Wages — Jun 2023', '', '54.80', '-22.40'],
        ['01-Jul-2023', 'NEFT — International Distribution', '55.00', '', '32.60'],
        ['18-Aug-2023', 'Vendor Payment — Marketing', '', '28.00', '4.60'],
        ['25-Sep-2023', 'Intra-Company Transfer — ZEEL Dubai', '35.00', '', '39.60'],
        ['10-Oct-2023', 'RTGS — Round Transfer — Subros Ltd.', '', '50.00', '-10.40'],
        ['05-Dec-2023', 'Q3 Advertising Revenue Reconciliation', '80.00', '', '69.60'],
        ['22-Jan-2024', 'HDFC CC Limit Repayment', '', '45.00', '24.60'],
        ['15-Feb-2024', 'Salary & Wages — Feb 2024', '', '56.20', '-31.60'],
        ['28-Mar-2024', 'Final TDS Payout to Govt', '', '7.90', '-39.50'],
        ['31-Mar-2024', 'GST Refund Credit — Misc.', '31.00', '', '-8.50'],
    ]
    story.append(tbl(txn_data, col_widths=[2.5*cm, 6*cm, 2.5*cm, 2.5*cm, 3*cm]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Risk Flags Identified by Bank Analytics", H2))
    story.append(Paragraph(
        "* THREE round-figure transactions of Rs. 50 Crore detected (28-May-2023, 10-Oct-2023, "
        "12-Apr-2023) — classified as potential structured transfers, flagged for AML review.", WARN))
    story.append(Paragraph(
        "* Negative closing balance indicates overdraft utilisation beyond sanctioned limit.", WARN))
    story.append(Paragraph(
        "* Outflows exceed inflows by Rs. 25 Crores — deteriorating liquidity position.", WARN))
    story.append(Paragraph(
        "* Intra-company transfer to ZEEL Dubai without clear commercial documentation flagged.", WARN))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Bank Officer Certification: Rohan Mehta | Grade: SM-III | Date: 05-Apr-2024", SMALL))

    doc.build(story)
    print(f"Created: {path}")

# ─────────────────────────────────────────────────────────────────────────────
# 3. GSTR-3B
# ─────────────────────────────────────────────────────────────────────────────
def doc3():
    path = os.path.join(OUT_DIR, 'mock_zee_gstr3b.pdf')
    doc = SimpleDocTemplate(path, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []
    story.append(Paragraph("FORM GSTR-3B", H1))
    story.append(Paragraph("Monthly Return Summary (Consolidated — FY 2023-24)", H1))
    story.append(Spacer(1, 6))
    info = [
        ['GSTIN:', '27AAACZ0503R1ZS'],
        ['Legal Name:', 'Zee Entertainment Enterprises Ltd.'],
        ['Trade Name:', 'ZEE Entertainment'],
        ['State/UT:', '27 — Maharashtra'],
        ['Return Period:', 'April 2023 to March 2024 (Annual Aggregated)'],
        ['Filing Status:', 'Filed with Delay — 3 months average delay'],
        ['Date of Last Filing:', '18-May-2024 (FY2024 Q4)'],
    ]
    story.append(tbl(info, col_widths=[5*cm, 11.5*cm], header_row=False))
    story.append(Spacer(1, 12))
    story.append(hr())

    story.append(Paragraph("3.1 Details of Outward Supplies and Inward Supplies Liable to Reverse Charge", H2))
    outward = [
        ['Nature of Supply', 'Taxable Value (Rs. Cr)', 'Integrated Tax', 'Central Tax', 'State Tax'],
        ['(a) Outward taxable supplies (other than zero rated, nil rated & exempted)', '820.00', '98.40', '24.60', '24.60'],
        ['(b) Outward taxable supplies (zero rated)', '68.50', '0', '0', '0'],
        ['(c) Other outward taxable supplies (nil rated, exempted)', '15.20', '0', '0', '0'],
        ['(d) Inward supplies (liable to reverse charge)', '12.40', '2.23', '0', '0'],
        ['(e) Non-GST outward supplies', '8.90', '', '', ''],
        ['TOTAL OUTPUT TAX LIABILITY', '', '100.63', '24.60', '24.60'],
        ['TOTAL OUTPUT TAX (Effective)', '820.00', '147.60 (Cr)', '', ''],
    ]
    story.append(tbl(outward, col_widths=[7*cm, 3*cm, 2.5*cm, 2.5*cm, 2*cm]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("4. Eligible ITC (Input Tax Credit) Claimed", H2))
    itc = [
        ['ITC Category', 'Integrated Tax (Cr)', 'Central Tax (Cr)', 'State Tax (Cr)', 'Total (Cr)'],
        ['(A) ITC Available (other than IGST on imports)', '110.00', '27.50', '27.50', '165.00'],
        ['(B) ITC Reversed (Rule 42/43)', '8.20', '2.05', '2.05', '12.30'],
        ['(C) Net ITC Available', '101.80', '25.45', '25.45', '152.70'],
    ]
    story.append(tbl(itc, col_widths=[6*cm, 3.5*cm, 3*cm, 3*cm, 2*cm]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "WARNING: ITC Claimed (Rs. 165.00 Cr) significantly exceeds eligible ITC Available "
        "per GSTR-2A reconciliation (Rs. 118.00 Cr). Excess ITC claim: Rs. 47.00 Cr (39.7% gap). "
        "This triggers a HIGH-RISK flag under GST compliance norms.", WARN))
    story.append(Spacer(1, 10))

    story.append(Paragraph("5. Payment of Tax", H2))
    payment = [
        ['Tax Head', 'Tax Payable (Cr)', 'Paid via ITC (Cr)', 'Paid via Cash (Cr)', 'Interest (Cr)'],
        ['Integrated Tax', '100.63', '95.00', '5.63', '4.20'],
        ['Central Tax', '24.60', '22.00', '2.60', '1.10'],
        ['State/UT Tax', '24.60', '22.00', '2.60', '1.10'],
        ['TOTAL', '149.83', '139.00', '10.83', '6.40'],
    ]
    story.append(tbl(payment, col_widths=[4.5*cm, 3.5*cm, 3.5*cm, 3.5*cm, 2*cm]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Late filing interest of Rs. 6.40 Cr charged on delayed returns across Q2 and Q3 FY2024.", WARN))

    doc.build(story)
    print(f"Created: {path}")

# ─────────────────────────────────────────────────────────────────────────────
# 4. GSTR-2A
# ─────────────────────────────────────────────────────────────────────────────
def doc4():
    path = os.path.join(OUT_DIR, 'mock_zee_gstr2a.pdf')
    doc = SimpleDocTemplate(path, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []
    story.append(Paragraph("FORM GSTR-2A", H1))
    story.append(Paragraph("Auto-Populated Inward Supplies (FY 2023-24)", H1))
    story.append(Spacer(1, 6))
    info = [
        ['GSTIN (Recipient):', '27AAACZ0503R1ZS'],
        ['Legal Name:', 'Zee Entertainment Enterprises Ltd.'],
        ['Return Period:', 'April 2023 to March 2024'],
        ['Auto-Populated As Of:', '25-May-2024 (GSTN Portal)'],
        ['Total Suppliers Reflected:', '156'],
    ]
    story.append(tbl(info, col_widths=[5.5*cm, 11*cm], header_row=False))
    story.append(Spacer(1, 12))
    story.append(hr())

    story.append(Paragraph("Section I — ITC Auto-Populated from Supplier Returns", H2))
    itc_avail = [
        ['Particulars', 'No. of Suppliers', 'Taxable Value (Cr)', 'IGST (Cr)', 'CGST (Cr)', 'SGST (Cr)', 'Total Tax (Cr)'],
        ['GSTR-1 Filed Suppliers', '141', '628.50', '65.00', '17.50', '17.50', '100.00'],
        ['GSTR-1 Pending/Not Filed', '15', '98.40', '11.00', '3.50', '3.50', '18.00'],
        ['ITC Available (Filed only)', '141', '628.50', '65.00', '17.50', '17.50', '100.00'],
        ['Total ITC Auto-Populated', '156', '726.90', '76.00', '21.00', '21.00', '118.00'],
    ]
    story.append(tbl(itc_avail, col_widths=[4.5*cm, 2.5*cm, 2.5*cm, 2*cm, 2*cm, 2*cm, 2*cm]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Section II — Reconciliation with GSTR-3B", H2))
    recon = [
        ['Reconciliation Item', 'Amount (Rs. Cr)'],
        ['ITC as per GSTR-2A (Auto-populated by GSTN)', '118.00'],
        ['ITC Claimed in GSTR-3B by assessee', '165.00'],
        ['EXCESS ITC Claimed (Potential Fraudulent Claim)', '47.00'],
        ['Excess ITC as % of Available ITC', '39.7%  HIGH RISK'],
        ['Threshold per GST Circular 183/15/2022', '5% or Rs. 5 Cr (whichever lower)'],
        ['Status', 'NON-COMPLIANT — Department Notice Likely'],
    ]
    story.append(tbl(recon, col_widths=[10*cm, 6.5*cm]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "CRITICAL FLAG: Excess ITC of Rs. 47 Crores (39.7% of available ITC) has been claimed "
        "beyond auto-populated GSTR-2A data. This significantly exceeds the permissible limit. "
        "GST Department (CBIC) has the authority to initiate demand & recovery proceedings "
        "under Section 73/74 of the CGST Act, 2017. A show-cause notice may have been or "
        "is likely to be issued.", WARN))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Section III — Top 10 Suppliers by ITC Value", H2))
    suppliers = [
        ['Supplier GSTIN', 'Supplier Name', 'ITC Available (Cr)', 'Filed?'],
        ['27AADCS3715R1Z4', 'Sony LIV Digital Pvt Ltd', '18.50', 'Yes'],
        ['27AABCS2581R1Z5', 'Star India Pvt Ltd', '14.80', 'Yes'],
        ['07AAECS3715R1ZP', 'Reliance Jio Infocomm Ltd', '12.40', 'Yes'],
        ['27AAKCA8837H1Z3', 'Viacom18 Media Pvt Ltd', '9.60', 'Yes'],
        ['27AAMCZ4578D1Z8', 'Essel Group Services', '8.90', 'NO — PENDING'],
        ['29AABCT1332L1Z1', 'Times Network Pvt Ltd', '7.20', 'Yes'],
        ['27AADCS3715R1Z9', 'Prime Focus Technologies', '6.80', 'Yes'],
        ['27AAKCP0345B1Z2', 'Phantasm Productions', '5.90', 'NO — PENDING'],
        ['27AAECG8843J1Z6', 'Gray Matters Capital India', '4.20', 'Yes'],
        ['19AABCV2154N1Z7', 'Voot Select Content Studio', '3.90', 'Yes'],
    ]
    story.append(tbl(suppliers, col_widths=[4.5*cm, 7*cm, 3.5*cm, 2*cm]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Note: 2 Essel Group-related entities (suppliers) have NOT filed GSTR-1 returns for "
        "FY2024, making their ITC unavailable for claim. ZEEL has nonetheless claimed ITC "
        "from these entities in GSTR-3B.", WARN))

    doc.build(story)
    print(f"Created: {path}")

# ─────────────────────────────────────────────────────────────────────────────
# 5. SANCTION LETTER
# ─────────────────────────────────────────────────────────────────────────────
def doc5():
    path = os.path.join(OUT_DIR, 'mock_zee_sanction_letter.pdf')
    doc = SimpleDocTemplate(path, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []
    story.append(Paragraph("HDFC BANK LIMITED", H1))
    story.append(Paragraph("Credit Sanction Letter", H1))
    story.append(Paragraph("Corporate Banking — Large Account Group", H1))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Ref: HDFC/CBG/MUM/ZEE/2024-25/00842 | Date: 12-Apr-2024", SMALL))
    story.append(hr())

    story.append(Paragraph("To:", BOLD))
    story.append(Paragraph("The Board of Directors", BODY))
    story.append(Paragraph("Zee Entertainment Enterprises Ltd.", BODY))
    story.append(Paragraph("18th Floor, A Wing, Marathon Futurex,", BODY))
    story.append(Paragraph("N. M. Joshi Marg, Lower Parel, Mumbai - 400013", BODY))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Dear Sir/Madam,", BODY))
    story.append(Paragraph(
        "With reference to your credit application and subsequent discussions, "
        "we are pleased to inform you of the renewal and modification of your existing "
        "credit facilities on the following terms and conditions:", BODY))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Credit Facility Details", H2))
    facility = [
        ['Parameter', 'Details'],
        ['Facility Type', 'Cash Credit (CC) / Working Capital Demand Loan'],
        ['Sanctioned Limit', 'Rs. 500 Crores'],
        ['Sub-Limit — WCDL', 'Rs. 200 Crores (within overall CC limit)'],
        ['Rate of Interest', '13.50% p.a. (HDFC Bank MCLR + 3.75%)'],
        ['Base Rate / MCLR', '9.75% (1-Year MCLR as of April 2024)'],
        ['Spread / Margin', '3.75% (Risk Premium — HIGH risk category)'],
        ['Repayment Period', 'Demand (CC) / 6 months rolling (WCDL)'],
        ['Validity / Renewal', '12 months — due for review by April 2025'],
        ['Drawing Power', 'Based on monthly stock & debtor statements'],
        ['Processing Fee', '0.50% of limit = Rs. 2.50 Crores (one-time)'],
    ]
    story.append(tbl(facility, col_widths=[5.5*cm, 11*cm]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Security & Collateral", H2))
    security = [
        ['Security Type', 'Description', 'Value (Cr)'],
        ['Primary', 'Charge on current assets (receivables, stock)', '1,480.00'],
        ['Collateral 1', 'Equitable mortgage of owned content library', '850.00'],
        ['Collateral 2', 'Corporate Guarantee by Essel Group entities', 'Rs. 300 Cr'],
        ['Pledge', 'Pledge of promoter shares (18.4% of equity)', 'Rs. ~480 Cr (mkt)'],
        ['Personal Gty', 'Personal Guarantee of Managing Director', '—'],
    ]
    story.append(tbl(security, col_widths=[3.5*cm, 10*cm, 3*cm]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Special Conditions & Covenants", H2))
    story.append(Paragraph(
        "1. DSCR Covenant: The Company shall maintain a minimum DSCR of 1.10x on a trailing "
        "12-month basis. Current DSCR of 0.82x is a covenant breach — Waiver Letter No. "
        "HDFC/WAI/2024/0091 dated 10-Mar-2024 in place for one year only.", WARN))
    story.append(Paragraph(
        "2. Reporting: Monthly stock statements, quarterly financial results, and annual "
        "audited financials within 90 days of year-end are mandatory.", BODY))
    story.append(Paragraph(
        "3. NCLT Matters: Any adverse order in NCLT proceedings (Case No. CP/1234/2023) "
        "triggering a liability in excess of Rs. 100 Crores shall constitute an Event of "
        "Default and may result in recall of the entire outstanding.", WARN))
    story.append(Paragraph(
        "4. Promoter Pledge Cap: Promoter pledging shall not exceed 70% of promoter "
        "holding. Current pledging at 67.8% — close to covenant threshold.", WARN))
    story.append(Paragraph(
        "5. No Dividend: No dividend declaration shall be made without prior written "
        "consent of the Bank so long as any amounts remain outstanding.", BODY))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Sanctioning Authority: Credit Committee — Corporate Risk Division", SMALL))
    story.append(Paragraph(
        "Authorised Signatory: Rajesh Kumar Singhania | EVP — Corporate Banking", SMALL))
    story.append(Paragraph(
        "Date of Sanction: 12-April-2024 | Expiry: 11-April-2025", SMALL))

    doc.build(story)
    print(f"Created: {path}")

# ── Run all ──────────────────────────────────────────────────────────────────
print("Generating 5 Zee Entertainment test documents...")
doc1()
doc2()
doc3()
doc4()
doc5()
print(f"\nAll 5 documents saved to: {os.path.abspath(OUT_DIR)}")
