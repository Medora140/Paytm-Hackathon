from typing import List, Dict
import fitz  # PyMuPDF

def extract_text_by_pages(pdf_bytes: bytes) -> List[Dict[str, any]]:
    """
    Extracts text page-by-page from PDF bytes.
    Retains page numbers to support grounding and citations.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_data = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        text = page.get_text("text").strip()
        
        pages_data.append({
            "page_number": page_index + 1,
            "text": text if text else "[Scanned/Image page or empty content]"
        })

    doc.close()
    return pages_data

def format_document_for_llm(pages_data: List[Dict[str, any]]) -> str:
    """Formats pages into a single annotated prompt string."""
    formatted_blocks = []
    for page in pages_data:
        formatted_blocks.append(f"--- PAGE {page['page_number']} ---\n{page['text']}\n")
    return "\n".join(formatted_blocks)