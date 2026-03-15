import os
import time
import json
import requests
from requests.exceptions import RequestException
from dotenv import load_dotenv

def run_rest_api():
    load_dotenv(".env")
    api_key = os.getenv("PAGEINDEX_API_KEY")
    if not api_key:
        print("PAGEINDEX_API_KEY not found in .env")
        return
        
    base_url = "https://api.pageindex.ai"
    headers = {"api_key": api_key}
    
    with open("tests/fixtures/pageindex_doc_id.txt", "r") as f:
        doc_id = f.read().strip()
        
    print(f"Polling for {doc_id} to be ready...")
    
    # Retry helper to survive DNS failures
    def do_request(method, url, **kwargs):
        for attempt in range(5):
            try:
                if method == "GET":
                    return requests.get(url, **kwargs)
                elif method == "POST":
                    return requests.post(url, **kwargs)
            except RequestException as e:
                print(f"Network error (attempt {attempt+1}/5): {e}")
                time.sleep(5)
        raise Exception(f"Failed to connect after 5 attempts to {url}")
        
    timeout = 300
    start = time.time()
    
    # Check tree readiness
    is_ready = False
    while not is_ready:
        if time.time() - start > timeout:
            print("Timeout waiting for indexing.")
            return
            
        print(f"Checking index status...")
        res = do_request("GET", f"{base_url}/doc/{doc_id}/?type=tree&summary=False", headers=headers)
        if res.status_code == 200:
            data = res.json()
            if data.get("retrieval_ready"):
                is_ready = True
                print("Document is ready!")
                break
        else:
            print(f"Not ready yet (Status: {res.status_code})")
        time.sleep(5)
        
    query = "What is the total Revenue from Operations for the most recent financial year ended March 31, 2024, in Crores?"
    print(f"Submitting query: '{query}'")
    
    payload = {"doc_id": doc_id, "query": query, "thinking": True}
    res = do_request("POST", f"{base_url}/retrieval/", headers=headers, json=payload)
    
    if res.status_code != 200:
        print(f"Failed to submit query: {res.text}")
        return
        
    ret_id = res.json().get("retrieval_id")
    print(f"Retrieval ID: {ret_id}")
    
    # Poll for query response
    start = time.time()
    while True:
        if time.time() - start > timeout:
            print("Timeout waiting for query result.")
            return
            
        res = do_request("GET", f"{base_url}/retrieval/{ret_id}/", headers=headers)
        if res.status_code == 200:
            data = res.json()
            status = data.get("status")
            if status in ["completed", "failed"]:
                print("\n--- RAW PAGEINDEX RESPONSE ---")
                print(json.dumps(data, indent=2))
                break
            else:
                print(f"Query status: {status}")
        else:
            print(f"Failed to check query status: {res.text}")
        time.sleep(3)

if __name__ == "__main__":
    run_rest_api()
