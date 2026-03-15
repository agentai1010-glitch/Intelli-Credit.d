import fitz
import os

pdf_path = r"c:\Users\PRATIK SAWANT\Desktop\Intelli-Credit.d\mock_documents\Vivriti Capital\Annual Report FY 2024-25.pdf"
doc = fitz.open(pdf_path)

pages_to_extract = [231, 232, 233, 234]

for p in pages_to_extract:
    print(f"\n--- PAGE {p+1} ---")
    print(doc[p].get_text())
