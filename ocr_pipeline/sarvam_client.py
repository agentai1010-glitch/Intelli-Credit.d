import os
import time
import zipfile
import io
import json
import fitz  # PyMuPDF
from typing import Dict, Any

class SarvamExtractionError(Exception):
    def __init__(self, message: str, status_code: int = None):
        super().__init__(f"{message} (HTTP {status_code})")
        self.status_code = status_code

def extract_with_sarvam(pdf_path: str, page_number: int = None) -> Dict[str, Any]:
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        raise SarvamExtractionError("No SARVAM_API_KEY found", 401)

    try:
        from sarvamai import SarvamAI
    except ImportError:
        raise SarvamExtractionError("sarvamai SDK not installed", 500)

    client = SarvamAI(api_subscription_key=api_key)

    file_to_upload = pdf_path
    cleanup_file = False
    
    if page_number is not None:
        doc = fitz.open(pdf_path)
        single_page_doc = fitz.open()
        single_page_doc.insert_pdf(doc, from_page=page_number-1, to_page=page_number-1)
        temp_path = f"temp_page_{page_number}_{os.path.basename(pdf_path)}"
        single_page_doc.save(temp_path)
        single_page_doc.close()
        doc.close()
        file_to_upload = temp_path
        cleanup_file = True

    filename = os.path.basename(file_to_upload)

    job_id = None
    try:
        # 1. Initialise
        try:
            # Output format 'json' throws 400 so we omit it and use default which contains metadata jsons anyway
            init_res = client.document_intelligence.initialise(job_parameters={"language": "en-IN"})
            job_id = init_res.job_id
        except Exception as e:
            status_code = getattr(e, "status_code", getattr(e, "status", 400))
            if "Forbidden" in str(type(e)) or "403" in str(e): status_code = 403
            raise SarvamExtractionError(f"API Initialise Failed: {e}", status_code)
            
        # 2. Get upload urls
        try:
            ul_res = client.document_intelligence.get_upload_links(job_id=job_id, files=[filename])
            upload_url_details = ul_res.upload_urls[filename]
            upload_url = getattr(upload_url_details, 'file_url', str(upload_url_details))
        except Exception as e:
            raise SarvamExtractionError(f"Upload URL Failed: {e}", getattr(e, "status_code", 400))
            
        # 3. Upload file
        import requests
        with open(file_to_upload, "rb") as f:
            up_res = requests.put(upload_url, data=f, headers={"Content-Type": "application/pdf", "x-ms-blob-type": "BlockBlob"})
            if up_res.status_code not in (200, 201):
                raise SarvamExtractionError(f"File Upload Failed: {up_res.text}", up_res.status_code)
                
        # 4. Start
        try:
            client.document_intelligence.start(job_id=job_id)
        except Exception as e:
            raise SarvamExtractionError(f"Start Job Failed: {e}", getattr(e, "status_code", 400))
            
        # 5. Poll
        start_time = time.time()
        completed = False
        while time.time() - start_time < 60:
            status_res = client.document_intelligence.get_status(job_id=job_id)
            state = status_res.job_state
            
            if state == "Completed":
                completed = True
                break
            elif state == "Failed":
                raise SarvamExtractionError("Job failed on Sarvam side", 500)
                
            time.sleep(3)
            
        if not completed:
            raise SarvamExtractionError("Sarvam job timed out after 60 seconds", 408)
            
        # 6. Get download links
        try:
            dl_res = client.document_intelligence.get_download_links(job_id=job_id)
            dl_urls = dl_res.download_urls
            zip_obj = list(dl_urls.values())[0] if dl_urls else None
            zip_url = getattr(zip_obj, 'file_url', str(zip_obj))
            if not zip_url:
                raise SarvamExtractionError("No download URL returned from Sarvam", 500)
        except Exception as e:
            raise SarvamExtractionError(f"Download URL failed: {e}", getattr(e, "status_code", 400))
            
        # 7. Process result
        zip_resp = requests.get(zip_url, timeout=30)
        if zip_resp.status_code != 200:
            raise SarvamExtractionError("Failed to download result zip", zip_resp.status_code)
            
        raw_text_parts = []
        tables = []
        confidence = 1.0
        
        with zipfile.ZipFile(io.BytesIO(zip_resp.content)) as z:
            # Read metadata JSONs to assemble raw text
            json_files = sorted([name for name in z.namelist() if name.startswith('metadata/') and name.endswith('.json')])
            for jf_name in json_files:
                with z.open(jf_name) as jf:
                    data = json.load(jf)
                    for block in data.get("blocks", []):
                        if "text" in block:
                            raw_text_parts.append(block["text"])
                        if block.get("layout_tag") == "table":
                            tables.append(block)

        raw_text = "\n".join(raw_text_parts)

        return {
            "raw_text": raw_text,
            "tables": tables,
            "language_detected": "en-IN",
            "confidence": confidence
        }

    finally:
        if cleanup_file and os.path.exists(file_to_upload):
            os.remove(file_to_upload)
