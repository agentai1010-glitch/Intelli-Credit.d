from fpdf import FPDF
import os

def create_pdf(filename, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in content:
        pdf.cell(200, 10, txt=line, ln=True)
    
    output_path = os.path.join("mock_documents", "Vivriti Capital", filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)
    print(f"Created {output_path}")

# Mock Annual Report for Vivriti to bypass PageIndex Limit
create_pdf("mock_vivriti_annual_report.pdf", [
    "ANNUAL REPORT - VIVRITI CAPITAL LIMITED",
    "Financial Year: 2024-25",
    "Balance Sheet Highlights:",
    "Total Revenue from Operations: Rs. 15,000,000,000.00",
    "EBITDA: Rs. 1,500,000,000.00",
    "Net Profit After Tax: Rs. 120,000,000.00",
    "Total Equity (Net Worth): Rs. 15,000,000,000.00",
    "Total Borrowings (Existing Debt): Rs. 63,450,000,000.00",
    "Sector: Financial Services",
    "Auditor Qualification: Unqualified opinion."
])
