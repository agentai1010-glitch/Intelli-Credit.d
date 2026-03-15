import camelot
import pandas as pd
from typing import List
import json

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies post-cleaning logic to extracted tables:
    - Normalizes column names
    - Strips ₹, %, and newline characters
    """
    if df.empty:
        return df

    # Normalize column names: string format, replace newlines
    df.columns = [str(col).replace('\n', ' ').strip() for col in df.columns]
    
    # Strip whitespace, ₹, and % signs from all string cells
    # Convert dates or other specifics if desired.
    df = df.apply(lambda col: col.map(
        lambda x: str(x).replace('\n', ' ').replace('₹', '').replace('%', '').strip() if isinstance(x, str) else x
    ))
    
    return df

def extract_tables(pdf_path: str, mode: str = "stream", pages: str = "1-5") -> List[pd.DataFrame]:
    """
    Extracts tables from a PDF using Camelot.
    Fails fast: uses "stream" by default as it is much faster and doesn't require Ghostscript.
    """
    import threading
    
    # Camelot can hang on some malformed PDFs. We use a thread-based timeout.
    result = []
    error_container = [None]
    
    def target():
        try:
            # We use flavor=mode (stream by default)
            tables = camelot.read_pdf(pdf_path, pages=pages, flavor=mode)
            result.extend([t.df for t in tables])
        except Exception as e:
            error_container[0] = e

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout=30) # 30 second limit per file
    
    if thread.is_alive():
        print(f"[TABLES] Timeout (30s) reached for {pdf_path}. Skipping table extraction.")
        return []
        
    if error_container[0]:
        print(f"Error extracting tables from {pdf_path}: {error_container[0]}")
        return []
        
    cleaned_tables = []
    for df in result:
        if not df.empty:
            # Assume first row is header for generic cleaning
            new_header = df.iloc[0]
            df = df[1:].copy()
            df.columns = new_header
            
            cleaned_df = clean_dataframe(df)
            cleaned_tables.append(cleaned_df)
            
    return cleaned_tables

def export_tables_to_json(tables: List[pd.DataFrame]) -> str:
    """
    Converts list of DataFrames to a JSON string for UI preview or API output.
    """
    tables_dict = []
    for i, df in enumerate(tables):
        tables_dict.append({
            "table_index": i,
            "data": df.to_dict(orient="records")
        })
    return json.dumps(tables_dict, indent=2)
