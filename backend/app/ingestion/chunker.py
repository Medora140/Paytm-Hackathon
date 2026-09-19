import re
from typing import Any, Dict, List, Optional


class ClauseChunker:
    """
    Document-type-agnostic clause-level chunker.
    Splits extracted PDF pages into semantically coherent clause segments by headers,
    numbered clauses, or section breaks.
    Supports English and Hindi documents.
    Strictly preserves page_number and generates clause_label.
    """

    def __init__(self, max_chunk_chars: int = 1200, min_chunk_chars: int = 40):
        self.max_chunk_chars = max_chunk_chars
        self.min_chunk_chars = min_chunk_chars

        # Comprehensive pattern matching clauses, sections, headings across
        # English and Hindi policy documents, Mutual Funds, Loans, and Insurance
        self.header_pattern = re.compile(
            r"(?:(?<=\n)|^)"
            r"("
            r"(?:(?:Section|Clause|Article|Schedule|Part|धारा|अनुभाग|खंड|शर्त|नियम|परिशिष्ट)\s+[A-Z0-9\.\-\u0966-\u096F]+[^\n]{0,80})"
            r"|"
            r"(?:(?:\d{1,2}(?:\.\d{1,2}){0,3}|[\u0966-\u096F]{1,2}(?:\.[\u0966-\u096F]{1,2}){0,3})\.?\s+[A-Z\u0900-\u097F][^\n]{3,80})"
            r"|"
            r"(?:(?:[IVXLCDM]+)\.\s+[A-Z\u0900-\u097F][^\n]{3,80})"
            r"|"
            r"(?:[A-Z0-9\u0900-\u097F\s\/\&\(\)\-]{4,50}:)"
            r"|"
            r"(?:[A-Z\s]{5,60}(?=\n))"
            r")",
            re.MULTILINE
        )

    def chunk_pages(self, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Segments extracted pages into page-tagged clause chunks.
        pages_data format:
          [{"page_number": int, "text": str}, ...]
        Returns:
          [{"page_number": int, "clause_label": str, "text": str}, ...]
        """
        chunks: List[Dict[str, Any]] = []

        for page in pages_data:
            page_num = page.get("page_number", 1)
            raw_text = self._normalise_extracted_text(page.get("text") or "")

            if not raw_text:
                continue

            matches = list(self.header_pattern.finditer(raw_text))

            if not matches:
                # No distinct clause headers detected on this page
                self._chunk_plain_page(page_num, raw_text, chunks)
                continue

            # Process text before the first match
            first_match = matches[0]
            if first_match.start() > 0:
                pre_text = raw_text[:first_match.start()].strip()
                if len(pre_text) >= self.min_chunk_chars:
                    chunks.append({
                        "page_number": page_num,
                        "clause_label": f"Page {page_num} Overview",
                        "text": pre_text
                    })

            # Process each matched header block
            for i, match in enumerate(matches):
                header_raw = match.group().strip()
                clean_header = re.sub(r"[\s\:\-]+$", "", header_raw).strip()

                start = match.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
                clause_body = raw_text[start:end].strip()

                if not clause_body:
                    continue

                if len(clause_body) > self.max_chunk_chars:
                    # Subdivide oversized clause into smaller coherent paragraphs
                    sub_chunks = self._subdivide_text(clause_body, self.max_chunk_chars)
                    for part_idx, sub_text in enumerate(sub_chunks, 1):
                        chunks.append({
                            "page_number": page_num,
                            "clause_label": f"{clean_header} (Part {part_idx})",
                            "text": sub_text
                        })
                else:
                    if len(clause_body) >= self.min_chunk_chars or not chunks:
                        chunks.append({
                            "page_number": page_num,
                            "clause_label": clean_header,
                            "text": clause_body
                        })
                    else:
                        if chunks and chunks[-1]["page_number"] == page_num:
                            chunks[-1]["text"] += "\n\n" + clause_body
                        else:
                            chunks.append({
                                "page_number": page_num,
                                "clause_label": clean_header,
                                "text": clause_body
                            })

        return chunks

    @staticmethod
    def _normalise_extracted_text(text: str) -> str:
        """Repair common PDF/OCR artefacts before section detection and embedding."""
        text = text.replace("\u00ad", "")  # soft hyphen
        text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)  # hyphenated line wrap
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _chunk_plain_page(self, page_num: int, text: str, chunks_out: List[Dict[str, Any]]):
        """Chunks a page without header patterns by paragraph / length."""
        if len(text) <= self.max_chunk_chars:
            chunks_out.append({
                "page_number": page_num,
                "clause_label": f"Page {page_num} Content",
                "text": text
            })
            return

        paragraphs = text.split("\n\n")
        current_chunk = ""
        part_idx = 1

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 2 > self.max_chunk_chars and current_chunk:
                chunks_out.append({
                    "page_number": page_num,
                    "clause_label": f"Page {page_num} Part {part_idx}",
                    "text": current_chunk
                })
                part_idx += 1
                current_chunk = para
            else:
                current_chunk = f"{current_chunk}\n\n{para}".strip() if current_chunk else para

        if current_chunk:
            chunks_out.append({
                "page_number": page_num,
                "clause_label": f"Page {page_num} Part {part_idx}",
                "text": current_chunk
            })

    def _subdivide_text(self, text: str, max_chars: int) -> List[str]:
        """Subdivides long text by paragraph, danda (।), or line boundaries."""
        parts = []
        # Support splitting on double newlines or Hindi/English sentence breaks
        paras = re.split(r"(?<=[।\.\!\?])\s+|\n+", text)
        cur = ""
        for p in paras:
            p = p.strip()
            if not p:
                continue
            if len(cur) + len(p) + 1 > max_chars and cur:
                parts.append(cur)
                cur = p
            else:
                cur = f"{cur} {p}".strip() if cur else p
        if cur:
            parts.append(cur)
        return parts if parts else [text]
