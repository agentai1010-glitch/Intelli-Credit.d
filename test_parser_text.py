import os
from ocr_pipeline.pdf_parser import extract_layout_text
from ocr_pipeline.table_extractor import extract_tables
from ml_engine.smart_parser import classify_document_type, parse_by_type

mock_files = [
    "mock_annual_report.pdf",
    "mock_bank_statement.pdf",
    "mock_gstr2a.pdf",
    "mock_gstr3b.pdf",
    "mock_sanction_letter.pdf"
]

for f in mock_files:
    file_path = f"mock_documents/{f}"
    print(f"\n--- {f} ---")
    combined_text = ""
    
    text_blocks = extract_layout_text(file_path)
    if text_blocks:
        combined_text += " " + " ".join([b.get("text", "") for b in text_blocks])
        
    try:
        tables = extract_tables(file_path)
        tables_data = [t.to_dict(orient="records") for t in tables]
        for t_dict in tables_data:
            for row in t_dict:
                combined_text += " " + " ".join([str(v) for v in row.values()])
    except Exception as e:
        pass
        
    class_result = classify_document_type(combined_text, f)
    parsed_data = parse_by_type(combined_text, class_result["document_type"])
    
    with open("test_output.txt", "a", encoding="utf-8") as out_f:
        out_f.write(f"\n--- {f} ---\n")
        out_f.write(f"Type: {class_result['document_type']}\n")
        out_f.write(f"Parsed fields: {parsed_data.get('display', [])}\n")
        out_f.write(f"Combined Text: {combined_text}\n")
