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
        Uses PyMuPDF (fitz) for near-instant native text detection.
        """
        page_diagnostics = []
        total_native_chars = 0
        scanned_pages_count = 0

        # Fast path with PyMuPDF
        if fitz is not None:
            try:
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                num_pages = len(doc)
                for page_idx in range(num_pages):
                    page_num = page_idx + 1
                    page = doc[page_idx]
                    text = (page.get_text("text") or "").strip()
                    char_count = len(text)
                    total_native_chars += char_count
                    has_images = len(page.get_images()) > 0
                    is_scanned = char_count < self.min_char_threshold
                    if is_scanned:
                        scanned_pages_count += 1
                    page_diagnostics.append({
                        "page_number": page_num,
                        "char_count": char_count,
                        "has_images": has_images,
                        "is_scanned": is_scanned,
                        "preview": text[:100] if text else ""
                    })
                doc.close()
                is_overall_native = scanned_pages_count < (num_pages / 2.0) and total_native_chars > (self.min_char_threshold * max(1, num_pages // 2))
                return is_overall_native, page_diagnostics
            except Exception:
                pass

        # Fallback with pypdf
        reader = None
        num_pages = 0
        if pypdf is not None:
            try:
                reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
                num_pages = len(reader.pages)
            except Exception:
                pass

        for page_idx in range(num_pages):
            page_num = page_idx + 1
            text = ""
            if reader is not None:
                try:
                    text = (reader.pages[page_idx].extract_text() or "").strip()
                except Exception:
                    text = ""
            char_count = len(text)
            total_native_chars += char_count
            is_scanned = char_count < self.min_char_threshold
            if is_scanned:
                scanned_pages_count += 1
            page_diagnostics.append({
                "page_number": page_num,
                "char_count": char_count,
                "has_images": False,
                "is_scanned": is_scanned,
                "preview": text[:100] if text else ""
            })

        is_overall_native = scanned_pages_count < (max(1, num_pages) / 2.0) and total_native_chars > (self.min_char_threshold * max(1, num_pages // 2))
        return is_overall_native, page_diagnostics
