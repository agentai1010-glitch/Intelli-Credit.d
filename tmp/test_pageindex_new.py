import os
import sys
import time
import socket
import json
from dotenv import load_dotenv

# Add current dir to path
sys.path.append(os.getcwd())

load_dotenv('.env', override=True)
api_key = os.getenv('PAGEINDEX_API_KEY')
print(f"API Key: {api_key[:8]}...")

def dns_brute_force():
    print("DNS Brute Force...")
    for i in range(10):
        try:
            socket.gethostbyname("api.pageindex.ai.")
            socket.gethostbyname("api.pageindex.ai")
            print(f"DNS Success on attempt {i+1}")
            return True
        except Exception as e:
            print(f"DNS Attempt {i+1} failed: {e}")
            time.sleep(2)
    return False

if not dns_brute_force():
    print("FATAL: DNS refuses to resolve.")
    sys.exit(1)

from pageindex import PageIndexClient
from ml_engine.pageindex_extractor import run_query, parse_indian_number

client = PageIndexClient(api_key=api_key)
pdf_path = r"mock_documents/Vivriti Capital/Annual Report FY 2024-25.pdf"

print("\n--- SUBMISSION ---")
try:
    result = client.submit_document(file_path=pdf_path)
    doc_id = result.get("doc_id")
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

print("\n--- WAITING FOR INDEXING ---")
# LimitReached check
start = time.time()
while time.time() - start < 180:
    try:
        if client.is_retrieval_ready(doc_id):
            print("Ready!")
            break
    except Exception as e:
        print(f"Poll check: {e}")
        time.sleep(10)
else:
    print("Timeout")

print("\n--- REVENUE QUERY (thinking=True) ---")
q = "What is the total Revenue from Operations for FY2025 in this report? Answer ONLY the number in Crores."
ans = run_query(client, q, doc_id, thinking=True)
print(f"Raw: {ans}")
print(f"Parsed: {parse_indian_number(ans)}")
