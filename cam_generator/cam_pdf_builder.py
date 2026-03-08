import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.units import inch

# Colors
COLOR_PRIMARY = colors.HexColor('#1a3c5e')
COLOR_APPROVE = colors.HexColor('#27ae60')
COLOR_WATCHLIST = colors.HexColor('#e8a020')
COLOR_REJECT = colors.HexColor('#c0392b')

def safe_str(val):
    if val is None or val == "": 
        return "Not provided"
    return str(val)

def generate_sanction_terms_box(decision: str, loan_limit_cr, interest_rate, tenure_months: int, conditions: list):
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TermsTitle',
        parent=styles['Heading3'],
        textColor=COLOR_PRIMARY,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )
    
    decision_up = decision.upper()
    if decision_up == "APPROVE":
        bg_color = COLOR_APPROVE
    elif decision_up == "WATCHLIST":
        bg_color = COLOR_WATCHLIST
    else:
        bg_color = COLOR_REJECT

    elements = []
    
    cond_str = "<br/>".join([f"- {c}" for c in conditions]) if conditions else "None specified"
    
    data = [
        [Paragraph(f"<b>Sanction Decision: {decision_up}</b>", ParagraphStyle('W', textColor=colors.white, fontName='Helvetica-Bold'))],
        [Paragraph(f"<b>Facility Limit:</b> {safe_str(loan_limit_cr)}<br/><b>Interest Rate:</b> {safe_str(interest_rate)}<br/><b>Tenure:</b> {tenure_months} months", styles['Normal'])],
        [Paragraph(f"<b>Conditions:</b><br/>{cond_str}", styles['Normal'])]
    ]
    
    t = Table(data, colWidths=['100%'])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), bg_color),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
    ]))
    
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Sanction Terms", title_style))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    return elements

class MyDocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if flowable.__class__.__name__ == 'Paragraph':
            text = flowable.getPlainText()
            style = flowable.style.name
            if style == 'Heading1':
                self.notify('TOCEntry', (0, text, self.page))
            elif style == 'Heading2':
                self.notify('TOCEntry', (1, text, self.page))

def build_cam_pdf(
    output_path: str,
    company_name: str,
    cin: str,
    date_str: str,
    analyst_name: str,
    risk_score: int,
    decision: str,
    sections: dict,
    financials: dict = None,
    shap_chart_path: str = None,
    gst_data: dict = None,
    gst_flags: list = None,
    regulatory_flags: list = None,
    loan_limit_cr: float = 0,
    interest_rate: float = 0,
    tenure_months: int = 0,
    conditions: list = None,
    score_waterfall: dict = None
):
    doc = MyDocTemplate(output_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    h1 = ParagraphStyle('Heading1', parent=styles['Heading1'], fontName='Helvetica-Bold', textColor=COLOR_PRIMARY, spaceAfter=14)
    h2 = ParagraphStyle('Heading2', parent=styles['Heading2'], fontName='Helvetica-Bold', textColor=COLOR_PRIMARY, spaceAfter=10)
    normal = ParagraphStyle('Normal', parent=styles['Normal'], fontName='Helvetica', spaceAfter=10, leading=14)
    
    elements = []
    
    # Cover Page
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph(f"<b>CREDIT APPRAISAL MEMORANDUM</b>", ParagraphStyle('CoverTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=24, textColor=COLOR_PRIMARY)))
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(f"<b>Company:</b> {safe_str(company_name)}", ParagraphStyle('CoverSub', parent=styles['Heading2'], fontName='Helvetica', alignment=1)))
    elements.append(Paragraph(f"<b>CIN:</b> {safe_str(cin)}", ParagraphStyle('CoverSub', parent=styles['Normal'], fontName='Helvetica', alignment=1)))
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(f"<b>Date:</b> {safe_str(date_str)}", styles['Normal']))
    elements.append(Paragraph(f"<b>Analyst:</b> {safe_str(analyst_name)}", styles['Normal']))
    
    decision_up = safe_str(decision).upper()
    if decision_up == "APPROVE":
        badge_color = COLOR_APPROVE
    elif decision_up == "WATCHLIST":
        badge_color = COLOR_WATCHLIST
    else:
        badge_color = COLOR_REJECT
        
    badge = Table([[f"Risk Score: {risk_score}\nDecision: {decision_up}"]], colWidths=[200], rowHeights=[60])
    badge.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), badge_color),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('BOX', (0,0), (-1,-1), 1, badge_color),
        ('CORNER_RADIUS', (0,0), (-1,-1), 10)
    ]))
    elements.append(Spacer(1, 0.5*inch))
    elements.append(badge)
    elements.append(PageBreak())
    
    # TOC (basic placeholder if multi-pass isn't set up, Platypus native TOC requires multiple build passes, skipping complex setup for brevity, adding static title)
    elements.append(Paragraph("Table of Contents", h1))
    elements.append(Paragraph("1. Executive Summary", normal))
    elements.append(Paragraph("2. Score Waterfall Computation", normal))
    elements.append(Paragraph("3. Character (Management & Promoters)", normal))
    elements.append(Paragraph("4. Capacity (Financial Repayment)", normal))
    elements.append(Paragraph("5. Capital (Net Worth & Leverage)", normal))
    elements.append(Paragraph("6. Collateral (Security Coverage)", normal))
    elements.append(Paragraph("7. Conditions (Macro & Industry)", normal))
    elements.append(Paragraph("8. AI Risk Insights & SHAP", normal))
    elements.append(PageBreak())
    
    # Sections
    section_titles = [
        "Executive Summary",
        "Score Waterfall Computation",
        "Character (Management & Promoters)",
        "Capacity (Financial Repayment)",
        "Capital (Net Worth & Leverage)",
        "Collateral (Security Coverage)",
        "Conditions (Macro & Industry)",
        "AI Risk Insights & SHAP"
    ]
    
    for i, title in enumerate(section_titles):
        elements.append(Paragraph(f"{i+1}. {title}", h1))
        content = sections.get(title, "Information pending analytical review.")
        elements.append(Paragraph(content.replace('\n', '<br/>'), normal))
        elements.append(Spacer(1, 10))
        
        # Add tables to specific sections
        if title == "Score Waterfall Computation":
            if score_waterfall:
                base_score = score_waterfall.get("baseScore", 76)
                gst_reconciliation = score_waterfall.get("reconciliationScore", 58)
                gst_impact = -1 * int(round((100 - gst_reconciliation) * 0.18))
                qual_delta = score_waterfall.get("qualitativeDelta", -30)
                reg_score = score_waterfall.get("regulatoryScore", 85)
                
                reg_impact = 0
                if reg_score < 60:
                    reg_impact = -20
                elif reg_score < 80:
                    reg_impact = -5
                
                # Running scores for each stage
                gst_running = base_score + gst_impact
                qual_running = gst_running + qual_delta
                reg_running = qual_running + reg_impact
                final_score = score_waterfall.get("finalScore", reg_running)
                
                wf_data = [
                    ["Component", "Impact", "Running Score"],
                    ["LightGBM Base Score", f"+{base_score}", str(base_score)],
                    ["GST Reconciliation", f"{gst_impact}", str(gst_running)],
                    ["Qualitative Adjustment", f"{qual_delta}", str(qual_running)],
                    ["Regulatory Intelligence", f"{reg_impact}", str(reg_running)],
                    ["FINAL SCORE", "—", f"{final_score} / {decision}"]
                ]
                
                t = Table(wf_data, colWidths=[200, 100, 150])
                t_style = [
                    ('BACKGROUND', (0,0), (-1,0), COLOR_PRIMARY),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
                ]
                
                # Apply row backgrounds
                for r_idx, row in enumerate(wf_data[1:-1], 1):
                    impact_val = row[1]
                    if impact_val.startswith("-") and impact_val != "-0":
                        t_style.append(('BACKGROUND', (0, r_idx), (-1, r_idx), colors.HexColor('#fdf0f0')))
                    else:
                        t_style.append(('BACKGROUND', (0, r_idx), (-1, r_idx), colors.white))
                        
                # Ensure the final row is dark navy with appropriate colors
                if decision_up == "APPROVE": dec_color = COLOR_APPROVE
                elif decision_up == "REJECT": dec_color = COLOR_REJECT
                else: dec_color = COLOR_WATCHLIST
                
                t_style.append(('BACKGROUND', (0, -1), (-1, -1), COLOR_PRIMARY))
                t_style.append(('TEXTCOLOR', (0, -1), (-2, -1), colors.white))
                t_style.append(('TEXTCOLOR', (-1, -1), (-1, -1), dec_color))
                t_style.append(('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'))
                
                t.setStyle(TableStyle(t_style))
                elements.append(t)
                elements.append(Spacer(1, 10))

        if title == "Capacity (Financial Repayment)":
            if financials:
                pass # Add financial table here if needed
            if gst_data and gst_flags:
                elements.append(Paragraph("GST Reconciliation Variance", h2))
                
                # Table A: GST Validation Summary
                gst_table_data = [
                    ["Metric", "GST Declared", "Bank Statement", "Variance"],
                    ["Quarterly Revenue", f"Rs.{gst_data.get('gstr3b_turnover_cr', '3.85')}Cr", f"Rs.{gst_data.get('bank_credits_cr', '3.55')}Cr", f"{gst_data.get('revenue_gap_pct', '8.45')}%"],
                    ["ITC Claimed", f"Rs.{gst_data.get('itc_claimed_lakhs', '58')}L", f"Available Rs.{gst_data.get('itc_available_lakhs', '42')}L", f"{gst_data.get('itc_gap_pct', '38.1')}%"]
                ]
                t1 = Table(gst_table_data, colWidths=[150, 100, 100, 100])
                t1.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), COLOR_PRIMARY),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
                ]))
                elements.append(t1)
                elements.append(Spacer(1, 15))
                
                # Table B: Flags Detected
                elements.append(Paragraph("Flags Detected", h2))
                flags_data = [["Flag", "Severity", "Score Penalty"]]
                for f in gst_flags:
                    flags_data.append([f.get("flag", "UNKNOWN"), f.get("severity", "MEDIUM"), str(f.get("score_penalty", "-0"))])
                
                t2 = Table(flags_data, colWidths=[200, 100, 150])
                t2_style = [
                    ('BACKGROUND', (0,0), (-1,0), COLOR_PRIMARY),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
                ]
                for r_idx, row in enumerate(flags_data[1:], 1):
                    sev = row[1].upper()
                    if sev == "HIGH": bg = colors.HexColor('#ffdddd')
                    elif sev == "MEDIUM": bg = colors.HexColor('#fff3cd')
                    else: bg = colors.white
                    t2_style.append(('BACKGROUND', (0, r_idx), (-1, r_idx), bg))
                    
                t2.setStyle(TableStyle(t2_style))
                elements.append(t2)
                elements.append(Spacer(1, 10))
                
        if title == "Character (Management & Promoters)":
            if regulatory_flags:
                elements.append(Paragraph("Regulatory Findings", h2))
                reg_table_data = [["Source", "Finding", "Severity", "Date"]]
                for row in regulatory_flags:
                    reg_table_data.append([row.get("source",""), row.get("finding",""), row.get("severity",""), row.get("date","")])
                t = Table(reg_table_data)
                
                # Dynamic row backgrounds based on severity
                t_style = [
                    ('BACKGROUND', (0,0), (-1,0), COLOR_PRIMARY),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
                ]
                for r_idx, row in enumerate(regulatory_flags):
                    sev = row.get("severity", "").upper()
                    if sev == "HIGH":
                        bg = colors.HexColor('#ffdddd')
                    elif sev == "MEDIUM":
                        bg = colors.HexColor('#fff3cd')
                    elif sev == "CLEAN":
                        bg = colors.HexColor('#d4edda')
                    else:
                        bg = colors.white
                    t_style.append(('BACKGROUND', (0, r_idx+1), (-1, r_idx+1), bg))
                t.setStyle(TableStyle(t_style))
                elements.append(t)
                elements.append(Spacer(1, 10))

        if title == "AI Risk Insights & SHAP":
            if shap_chart_path and os.path.exists(shap_chart_path):
                elements.append(Image(shap_chart_path, width=400, height=300))
    
    # Terms Box
    elements.extend(generate_sanction_terms_box(decision, loan_limit_cr, interest_rate, tenure_months, conditions))
    
    doc.build(elements)
    return output_path

if __name__ == "__main__":
    elements = generate_sanction_terms_box("APPROVE", 7.225, 11.25, 12, ["Execution of MFA", "Audited financials required"])
    print("Function runs without error.")
    print("ReportLab elements returned:", [e.__class__.__name__ for e in elements])
