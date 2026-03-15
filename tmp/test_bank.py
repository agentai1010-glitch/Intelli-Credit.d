import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_engine.smart_parser import llm_extract_fields
from ocr_pipeline.pdf_parser import extract_layout_text
from dotenv import load_dotenv

load_dotenv()

fpath = "mock_documents/zee/mock_zee_bank_statement.pdf"
fname = "mock_zee_bank_statement.pdf"

print(f"Extracting {fname}...")
blocks = extract_layout_text(fpath)
text = " ".join([b.get("text", "") for b in blocks])

res = llm_extract_fields(text, "BANK_STATEMENT")
print("\n--- EXTRACTION RESULT ---")
print(json.dumps(res, indent=2))
