import io
from typing import Any, Dict, List, Tuple
try:
    import pypdf
except ImportError:
    pypdf = None
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


class PDFTypeDetector:
    """
    Detects whether a PDF is text-native or scanned/image-based.
    Inspects page-by-page text density and image contents.
    """

    def __init__(self, min_char_threshold: int = 40):
        self.min_char_threshold = min_char_threshold

    def inspect_pdf(self, pdf_bytes: bytes) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Analyzes the PDF and returns:
          (is_native: bool, page_diagnostics: List[Dict])
        """
        page_diagnostics = []
        total_native_chars = 0
        scanned_pages_count = 0

        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            num_pages = len(reader.pages)
        except Exception:
            # Fallback to PyMuPDF if pypdf has parsing issues
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            num_pages = len(doc)
            doc.close()
            reader = None

        fitz_doc = None
        try:
            fitz_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception:
            pass

        for page_idx in range(num_pages):
            page_num = page_idx + 1
            text = ""

            # Try pypdf extraction first
            if reader is not None:
                try:
                    text = reader.pages[page_idx].extract_text() or ""
                except Exception:
                    text = ""

            # If empty or pypdf failed, try pymupdf
            if not text.strip() and fitz_doc is not None and page_idx < len(fitz_doc):
                try:
                    text = fitz_doc[page_idx].get_text("text") or ""
                except Exception:
                    text = ""

            clean_text = text.strip()
            char_count = len(clean_text)
            total_native_chars += char_count

            # Check if page has images
            has_images = False
            if fitz_doc is not None and page_idx < len(fitz_doc):
                try:
                    images = fitz_doc[page_idx].get_images()
                    has_images = len(images) > 0
                except Exception:
                    pass

            is_scanned = char_count < self.min_char_threshold
            if is_scanned:
                scanned_pages_count += 1

            page_diagnostics.append({
                "page_number": page_num,
                "char_count": char_count,
                "has_images": has_images,
                "is_scanned": is_scanned,
                "preview": clean_text[:100] if clean_text else ""
            })

        if fitz_doc is not None:
            fitz_doc.close()

        # Document is considered text-native if less than half the pages are scanned
        # and there is substantial native text across the document
        is_overall_native = scanned_pages_count < (num_pages / 2.0) and total_native_chars > (self.min_char_threshold * max(1, num_pages // 2))

        return is_overall_native, page_diagnostics
