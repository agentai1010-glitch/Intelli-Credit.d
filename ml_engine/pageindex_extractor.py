import re
import os
import time
import requests
from dotenv import load_dotenv  # type: ignore
from ml_engine.pageindex_queries import ANNUAL_REPORT_QUERIES  # type: ignore
from pageindex import PageIndexClient

# MONKEYPATCH to support 'thinking' parameter in SDK 0.2.6
def patched_chat_completions(self, messages, stream=False, doc_id=None, temperature=None, thinking=False, **kwargs):
    payload = {
        "messages": messages,
        "stream": stream,
        "thinking": thinking
    }
    if doc_id: payload["doc_id"] = doc_id
    if temperature is not None: payload["temperature"] = temperature
    
    response = requests.post(
        f"{self.BASE_URL}/chat/completions/",
        headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        json=payload,
        stream=stream
    )
    if response.status_code != 200:
        raise Exception(f"Failed to get chat completion: {response.text}")
    return response.json()

PageIndexClient.chat_completions = patched_chat_completions

def run_query(client, q, doc_id, thinking=False):
    import socket
    import time
    for attempt in range(3):
        try:
            # DNS Warmup
            try: 
                socket.gethostbyname("api.pageindex.ai.")
                socket.gethostbyname("api.pageindex.ai")
            except: 
                pass

            res = client.chat_completions(
                messages=[{"role": "user", "content": f"{q} Return ONLY the absolute numeric value or short text. No extra text or tables. If not found, say 'None'."}],
                doc_id=doc_id,
                temperature=0.0,
                thinking=thinking
            )
            if isinstance(res, dict) and "choices" in res and len(res["choices"]) > 0:
                return res["choices"][0]["message"].get("content", "")
        except Exception as e:
            print(f"[PAGEINDEX] Query attempt {attempt+1} failed: {e}")
            if "LimitReached" in str(e):
                time.sleep(10) # Heavy wait for rate limits
            elif attempt < 2:
                time.sleep(2)
    return None

def upload_to_pageindex(pdf_path: str, api_key: str) -> str:
    """
    Upload a PDF to PageIndex and wait until it's ready for retrieval.
    Returns the doc_id.
    """
    from pageindex import PageIndexClient  # type: ignore
    client = PageIndexClient(api_key=api_key)
    
    print(f"[PAGEINDEX] Uploading {os.path.basename(pdf_path)} to PageIndex...")
    result = client.submit_document(file_path=pdf_path)
    doc_id = result.get("doc_id", "")
    
    if not doc_id:
        print(f"[PAGEINDEX] ERROR: No doc_id returned from submit_document")
        return ""
    
    print(f"[PAGEINDEX] Got doc_id: {doc_id} -- waiting for processing...")
    
    # Poll until ready (max 90 seconds)
    start = time.time()
    while time.time() - start < 90:
        try:
            if client.is_retrieval_ready(doc_id):
                print(f"[PAGEINDEX] Document ready for retrieval in {time.time()-start:.1f}s")
                return doc_id
        except Exception as e:
            pass
        time.sleep(3)
    
    print(f"[PAGEINDEX] WARNING: Document not ready after 90s, proceeding anyway")
    return doc_id


def load_doc_id_or_submit(pdf_path: str) -> str:
    """
    Submits a new document for indexing (No caching to prevent cross-company data leakage).
    """
    load_dotenv(override=True)
    api_key = os.getenv('PAGEINDEX_API_KEY')
    if api_key:
        print(f"[PAGEINDEX] Key loaded (8 chars): {api_key[:8]}")

    if not api_key:
        print("[PAGEINDEX] ERROR: No PAGEINDEX_API_KEY for submission")
        return ""

    print(f"[PAGEINDEX] Submitting new document for indexing...")
    doc_id = upload_to_pageindex(pdf_path, api_key)
    
    return doc_id

def parse_indian_number(text):
    """Parse Indian formatted numbers from PageIndex responses into absolute rupees."""
    if not text: return None
    t = text.strip()
    t_lower = t.lower()

    if re.search(r'cr(ore)?s?', t_lower):
        factor = 1e7
        t = re.sub(r'cr(ore)?s?\.?', '', t, flags=re.IGNORECASE)
    elif re.search(r'l(akh)?s?', t_lower) and not t_lower.endswith('al'):
        factor = 1e5
        t = re.sub(r'l(akh)?s?\.?', '', t, flags=re.IGNORECASE)
    else:
        clean_check = re.sub(r'[^\d\.,]', '', t)
        numeric_part = re.sub(r'[^\d\.]', '', clean_check.replace(',', ''))
        try:
            raw_val = float(numeric_part) if numeric_part else 0
        except:
            raw_val = 0
        factor = 1.0 if raw_val > 1e8 else 1e7

    clean_val = re.sub(r'[^\d\.,]', '', t).replace(',', '').strip('.')
    if not clean_val: return None
    try:
        return float(clean_val) * factor
    except:
        return None

def extract_with_pageindex(doc_id: str, pdf_path: str = None, cleanup: bool = False) -> tuple:
    load_dotenv()
    api_key = os.getenv('PAGEINDEX_API_KEY')
    if api_key:
        print(f"[PAGEINDEX] Key loaded (8 chars): {api_key[:8]}")
    
    if not api_key:
        print("[PAGEINDEX] ERROR: No PAGEINDEX_API_KEY found in .env")
        return {}, doc_id
    
    if pdf_path and os.path.exists(pdf_path):
        fresh_doc_id = upload_to_pageindex(pdf_path, api_key)
        if fresh_doc_id:
            doc_id = fresh_doc_id
    
    if not doc_id or doc_id == "mock_doc_id":
        print("[PAGEINDEX] ERROR: No valid doc_id available.")
        return {}, doc_id
    
    from pageindex import PageIndexClient # type: ignore
    client = PageIndexClient(api_key=api_key)
    results = {}
    numeric_fields = ["revenue", "ebitda", "net_worth", "net_profit", "existing_debt"]

    for field, query in ANNUAL_REPORT_QUERIES.items():
        time.sleep(2) # Reduced from 15s to 2s
        raw_ans = run_query(client, query, doc_id, thinking=False)
        print(f"[PAGEINDEX RAW] {field:<20} -> {str(raw_ans).replace(chr(10),' ')[:120]}")

        ans_text = raw_ans or "No answer returned."
        if any(kw in ans_text.lower() for kw in ["none", "not mentioned", "not explicitly", "not provided", "not found", "n/a"]):
            val = None
        elif field in numeric_fields:
            val = parse_indian_number(ans_text)
        else:
            val = ans_text.strip()

        results[field] = val
        print(f"[PAGEINDEX] {field:<25} | PARSED: {val} | RAW: {str(ans_text).replace(chr(10), ' ')[:100]}")

    if cleanup:
        try: client.delete_document(doc_id)
        except: pass
    return results, doc_id
