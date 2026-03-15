import os
import time
from ocr_pipeline.ocr_utils import extract_document

# Path to the real Vivriti Capital Annual Report
pdf_path = r"c:\Users\PRATIK SAWANT\Desktop\Intelli-Credit.d\mock_documents\Vivriti Capital\Annual Report FY 2024-25.pdf"

from dotenv import load_dotenv
load_dotenv()
print(f"DEBUG: SARVAM_API_KEY set? {'Yes' if os.environ.get('SARVAM_API_KEY') else 'No'}")

print(f"\n--- Testing Extraction on Vivriti Capital Annual Report ---")
start_time = time.time()

# This should trigger the new foreground PageIndex path
results = extract_document(pdf_path, "ANNUAL_REPORT")

end_time = time.time()
duration = end_time - start_time

import json
print(f"\n--- EXTRACTION RESULTS (MERGED DICT) ---")
print(json.dumps(results, indent=2))

print(f"\nStatus: Pipeline Complete")
print(f"Total Time Taken: {duration:.2f} seconds")

# Logic to check if PageIndex or Sarvam won would be in the console logs from extract_document
