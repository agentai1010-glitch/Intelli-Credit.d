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

# Bank Statement
create_pdf("mock_vivriti_bank_statement.pdf", [
    "Bank Statement - Vivriti Capital Limited",
    "Account Number: 998877665544",
    "Period: April 2024 - March 2025",
    "Total Credits: Rs. 14,000,000,000.00",
    "Total Debits: Rs. 13,800,000,000.00",
    "Closing Balance: Rs. 200,000,000.00",
    "Narration: Business Transactions verified."
])

# GSTR-3B
create_pdf("mock_vivriti_gstr3b.pdf", [
    "FORM GSTR-3B - Monthly Return",
    "GSTIN: 33AAACV4123R1ZN",
    "Legal Name: Vivriti Capital Limited",
    "Financial Year: 2024-25",
    "Tax Period: Annual Summary (Mock)",
    "Total Turnover: Rs. 13,470,000,000.00",
    "Output Tax Liability: Rs. 2,420,000,000.00",
    "ITC Claimed: Rs. 1,980,000,000.00"
])

# GSTR-2A
create_pdf("mock_vivriti_gstr2a.pdf", [
    "FORM GSTR-2A - Auto-populated Return",
    "GSTIN: 33AAACV4123R1ZN",
    "Period: 2024-25",
    "ITC Available for matching: Rs. 2,100,000,000.00",
    "Total Number of Suppliers: 89",
    "Status: Fully reconciled (Mock)"
])

# Sanction Letter
create_pdf("mock_vivriti_sanction_letter.pdf", [
    "HDFC Bank - Sanction Letter",
    "To: Vivriti Capital Limited",
    "Date: April 15, 2024",
    "Subject: Sanction of Working Capital Facility",
    "Sanctioned Facility Amount: Rs. 5,000,000,000.00",
    "Interest Rate: 9.5% p.a.",
    "Type of Facility: Cash Credit / Working Capital Loan",
    "Security: Pro-note and Book Debts"
])
