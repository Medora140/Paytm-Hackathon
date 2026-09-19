import io
import os
import logging
from typing import Any, Dict, List, Optional
from PIL import Image
import pypdf
import fitz  # PyMuPDF
import pytesseract

from app.ingestion.detector import PDFTypeDetector

logger = logging.getLogger(__name__)

# Search for tesseract executable in standard locations if not already set
POSSIBLE_TESSERACT_PATHS = [
    os.getenv("TESSERACT_CMD", ""),
    os.getenv("TESSERACT_CMD_PATH", ""),
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    r"C:\Users\Medora Gomes\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
]
for p in POSSIBLE_TESSERACT_PATHS:
    if p and os.path.isfile(p):
        pytesseract.pytesseract.tesseract_cmd = p
        break


class PDFTextExtractor:
    """
    Extracts text page-by-page from PDF documents.
    Primary extractor is pypdf with PyMuPDF fallback.
    Automatically triggers OCR (Tesseract) on pages detected as scanned/image.
    """

    def __init__(self, min_char_threshold: int = 40):
        self.min_char_threshold = min_char_threshold
        self.detector = PDFTypeDetector(min_char_threshold=min_char_threshold)

    def extract(self, pdf_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extracts text from each page, falling back to OCR when scanned.
        Returns a list of dicts:
          [{"page_number": int, "text": str, "is_ocr": bool, "char_count": int}, ...]
        """
        _, page_diagnostics = self.detector.inspect_pdf(pdf_bytes)

        # Open with pypdf and fitz
        pypdf_reader = None
        try:
            pypdf_reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        except Exception as e:
            logger.warning("pypdf could not open PDF stream: %s", e)

        fitz_doc = None
        try:
            fitz_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as e:
            logger.warning("PyMuPDF could not open PDF stream: %s", e)

        num_pages = len(page_diagnostics)
        extracted_pages = []

        for diag in page_diagnostics:
            page_idx = diag["page_number"] - 1
            page_num = diag["page_number"]
            is_scanned = diag["is_scanned"]
            page_text = ""
            is_ocr = False

            # If not scanned, extract native text
            if not is_scanned:
                if pypdf_reader and page_idx < len(pypdf_reader.pages):
                    try:
                        page_text = pypdf_reader.pages[page_idx].extract_text() or ""
                    except Exception as e:
                        logger.debug("pypdf error on page %s: %s", page_num, e)

                if not page_text.strip() and fitz_doc and page_idx < len(fitz_doc):
                    try:
                        page_text = fitz_doc[page_idx].get_text("text") or ""
                    except Exception as e:
                        logger.debug("fitz error on page %s: %s", page_num, e)

            # If page is marked scanned or native text was unexpectedly empty
            if is_scanned or len(page_text.strip()) < self.min_char_threshold:
                fitz_page = fitz_doc[page_idx] if fitz_doc and page_idx < len(fitz_doc) else None
                ocr_text = self._run_ocr_on_page(page_idx, fitz_page)
                if ocr_text and ocr_text.strip():
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

        if fitz_doc is not None:
            fitz_doc.close()

        return extracted_pages

    def _run_ocr_on_page(self, page_idx: int, fitz_page: Optional[Any]) -> str:
        """
        Renders the page to a raster pixmap and applies Tesseract OCR.
        """
        if fitz_page is None:
            return ""

        try:
            # Render page to image at 150 DPI for balanced speed & accuracy
            pix = fitz_page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_bytes))

            # Run pytesseract OCR
            text = pytesseract.image_to_string(image)
            return text.strip()
        except pytesseract.TesseractNotFoundError:
            logger.warning(
                "Tesseract binary not found in PATH or standard directories. OCR fallback skipped."
            )
            return ""
        except Exception as e:
            logger.warning("OCR failed on page %s: %s", page_idx + 1, e)
            return ""
