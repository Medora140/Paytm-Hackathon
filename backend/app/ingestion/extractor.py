import io
import os
import logging
from typing import Any, Dict, List, Optional
try:
    from PIL import Image
except ImportError:
    Image = None
try:
    import pypdf
except ImportError:
    pypdf = None
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
try:
    import pytesseract
except ImportError:
    pytesseract = None

from app.ingestion.detector import PDFTypeDetector

logger = logging.getLogger(__name__)

# Search for tesseract executable in standard locations if not already set
POSSIBLE_TESSERACT_PATHS = [
    os.getenv("TESSERACT_CMD", ""),
    os.getenv("TESSERACT_CMD_PATH", ""),
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
]
for p in POSSIBLE_TESSERACT_PATHS:
    if pytesseract is not None and p and os.path.isfile(p):
        pytesseract.pytesseract.tesseract_cmd = p
        break


class PDFTextExtractor:
    """
    Extracts text page-by-page from PDF documents.
    Primary extractor is pypdf with PyMuPDF fallback.
    Automatically triggers OCR (Tesseract) on pages detected as scanned/image.
    Supports multilingual documents in Hindi and English.
    """

    def __init__(self, min_char_threshold: int = 40):
        self.min_char_threshold = min_char_threshold
        self.detector = PDFTypeDetector(min_char_threshold=min_char_threshold)

    def extract(self, pdf_bytes: bytes) -> List[Dict[str, Any]]:
        """
        High-performance single-pass PDF text extractor:
        - Primary: PyMuPDF (fitz) in C/C++ (10x-50x faster than pypdf).
        - Fallback: pypdf if fitz is unavailable or fails.
        - OCR: Tesseract only when page text is below min_char_threshold.
        """
        extracted_pages: List[Dict[str, Any]] = []

        # 1. Try PyMuPDF (fitz) - blazing fast
        if fitz is not None:
            fitz_doc = None
            try:
                fitz_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                for page_idx in range(len(fitz_doc)):
                    page_num = page_idx + 1
                    page = fitz_doc[page_idx]
                    page_text = page.get_text("text") or ""
                    is_ocr = False

                    # If text is below threshold, try OCR fallback
                    if len(page_text.strip()) < self.min_char_threshold:
                        ocr_text = self._run_ocr_on_page(page_idx, page)
                        if ocr_text and len(ocr_text.strip()) > len(page_text.strip()):
                            page_text = ocr_text
                            is_ocr = True
                        elif not page_text.strip():
                            page_text = f"[Scanned/Image page {page_num} - Content unreadable without OCR]"

                    extracted_pages.append({
                        "page_number": page_num,
                        "text": page_text.strip(),
                        "is_ocr": is_ocr,
                        "char_count": len(page_text.strip())
                    })
                return extracted_pages
            except Exception as e:
                logger.warning("PyMuPDF fast extraction encountered error, falling back to pypdf: %s", e)
            finally:
                if fitz_doc is not None:
                    try:
                        fitz_doc.close()
                    except Exception:
                        pass

        # 2. Fallback: pypdf if fitz was unavailable or failed
        if pypdf is not None:
            try:
                reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
                for page_idx, page in enumerate(reader.pages):
                    page_num = page_idx + 1
                    page_text = page.extract_text() or ""
                    extracted_pages.append({
                        "page_number": page_num,
                        "text": page_text.strip() or f"[Page {page_num}]",
                        "is_ocr": False,
                        "char_count": len(page_text.strip())
                    })
                return extracted_pages
            except Exception as e:
                logger.error("pypdf extraction failed: %s", e)

        return extracted_pages

    def _run_ocr_on_page(self, page_idx: int, fitz_page: Optional[Any]) -> str:
        """
        Renders the page to a raster pixmap and applies Tesseract OCR with Hindi + English support.
        Skips immediately if pytesseract is not available or tesseract binary is not installed.
        """
        if fitz_page is None or pytesseract is None or Image is None:
            return ""

        try:
            # Render page at 130 DPI for optimal OCR speed and accuracy
            pix = fitz_page.get_pixmap(dpi=130)
            img_bytes = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_bytes))

            try:
                text = pytesseract.image_to_string(image, lang="hin+eng")
            except Exception:
                text = pytesseract.image_to_string(image)
            return text.strip()
        except (pytesseract.TesseractNotFoundError, Exception) as e:
            logger.debug("OCR skipped/failed on page %s: %s", page_idx + 1, e)
            return ""
