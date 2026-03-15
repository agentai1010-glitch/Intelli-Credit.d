import fitz  # PyMuPDF
from langdetect import detect, detect_langs

def extract_layout_text(pdf_path: str) -> list:
    """
    Extracts text by block/paragraph from a PDF using PyMuPDF (fitz)
    and returns a list of structured blocks.
    """
    extracted_blocks = []
    
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Failed to open PDF {pdf_path}: {e}")
        return extracted_blocks
        
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("blocks")
        
        for block in blocks:
            if block[6] == 0:  # 0 for text
                text = block[4].strip()
                if not text:
                    continue
                
                # OPTIMIZED: Skip per-block detection for speed
                lang = "en"
                    
                block_info = {
                    "page": page_num + 1,
                    "bbox": [block[0], block[1], block[2], block[3]],
                    "text": text,
                    "language": lang
                }
                extracted_blocks.append(block_info)
                
    return extracted_blocks
