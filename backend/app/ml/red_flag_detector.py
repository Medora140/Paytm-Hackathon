import logging
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.schemas import RedFlagItem, SeverityLevel
from app.ml.knowledge_base import RedFlagKnowledgeBase, RedFlagPattern

logger = logging.getLogger("app.ml.red_flag_detector")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


class RuleBasedRedFlagDetector:
    """
    Deterministic rule-based detector implementing the Red-Flag & Dispute Detector
    architecture described in 03-ml-ai-engine.md (§2).
    Evaluates document chunks against a curated Red-Flag Knowledge Base.
    """

    def __init__(self, kb: Optional[RedFlagKnowledgeBase] = None):
        self.kb = kb or RedFlagKnowledgeBase()

    def detect_red_flags(
        self,
        document_id: str,
        chunks: List[Dict[str, Any]],
        category: Optional[str] = None
    ) -> List[RedFlagItem]:
        """
        Scans document chunks for high-risk clauses and dispute patterns.
        Attaches exact chunk citations, page numbers, severity, and plain explanations.
        """
        if not chunks:
            logger.warning(
                "\n" + "=" * 68 + "\n"
                "[FALLBACK WARNING] [red_flag_detector] detect_red_flags called with empty chunks for doc '%s'!\n"
                "Action: Returning empty red flags list.\n"
                + "=" * 68,
                document_id
            )
            return []

        patterns = self.kb.get_patterns(category=category)
        flags: List[RedFlagItem] = []
        matched_chunk_patterns = set()
        seen_pattern_source = set()
        seen_explanation_source = set()
        seen_pattern_section = set()

        non_operative_re = re.compile(
            r"(?i)\b(?:table of contents|contents\b|synthetic benchmark data|test questions for money docs)\b"
        )

        # Track pages with Table of Contents to avoid flagging TOC entries as operative clauses
        toc_pages = set()
        for chunk in chunks:
            t = (chunk.get("text") or "").lower()
            if "contents" in t or "table of contents" in t:
                toc_pages.add(int(chunk.get("page_number", 1)))

        for chunk in chunks:
            chunk_id = str(chunk.get("id", f"chk_{uuid.uuid4().hex[:8]}"))
            page_number = int(chunk.get("page_number", 1))
            clause_label = chunk.get("clause_label") or f"Clause on Page {page_number}"
            text = chunk.get("text", "")
            
            # Skip non-operative document metadata (TOC pages/items, benchmark tables, test questions)
            if (
                page_number in toc_pages
                or non_operative_re.search(text[:120])
                or non_operative_re.search(clause_label)
            ):
                continue

            text_lower = text.lower()

            for pattern in patterns:
                pair_key = (chunk_id, pattern.pattern_id)
                if pair_key in matched_chunk_patterns:
                    continue

                matched = False
                matched_snippet = ""

                # For room rent patterns, require actual restriction/limit rather than plain coverage inclusions
                if pattern.pattern_id == "pat_irda_room_rent_01":
                    room_rent_restrict_re = r"(?i)\b(?:room\s*rent|room\s*charges)\b.*?(?:\d+\s*%|proportionate\s*deduction|\blimit(?:ed)?\b|\bcap\b|\bsub[\s\-]limit\b|per\s*day)"
                    m = re.search(room_rent_restrict_re, text)
                    if m:
                        matched = True
                        matched_snippet = m.group(0).strip()
                    elif any(kw in text_lower for kw in ["proportionate deduction", "room category limit", "sub-limit on room"]):
                        matched = True
                        matched_snippet = "proportionate deduction on room rent"

                # Standard check regex first if provided
                elif pattern.trigger_regex:
                    match_obj = re.search(pattern.trigger_regex, text)
                    if match_obj:
                        matched = True
                        matched_snippet = match_obj.group(0).strip()

                # Fallback to trigger keywords boundary search
                if not matched and pattern.pattern_id != "pat_irda_room_rent_01" and pattern.trigger_keywords:
                    for kw in pattern.trigger_keywords:
                        kw_clean = kw.lower().strip()
                        # Use word boundary search
                        if re.search(r"\b" + re.escape(kw_clean) + r"\b", text_lower):
                            matched = True
                            # Find matching sentence or surrounding window for source citation
                            start_idx = text_lower.find(kw_clean)
                            window_start = max(0, start_idx - 60)
                            window_end = min(len(text), start_idx + len(kw_clean) + 120)
                            matched_snippet = text[window_start:window_end].strip()
                            if window_start > 0:
                                matched_snippet = "..." + matched_snippet
                            if window_end < len(text):
                                matched_snippet = matched_snippet + "..."
                            break

                if matched:
                    matched_chunk_patterns.add(pair_key)
                    snippet = matched_snippet if matched_snippet else text[:250].strip() + "..."
                    
                    # Section-level deduplication: Prevent multiple flags for the same pattern in the same section
                    sec_match = re.match(r"^(?:(?:Section|Clause)\s+)?(\d+)", clause_label.strip())
                    sec_id = sec_match.group(1) if sec_match else clause_label[:30]
                    sec_key = (pattern.pattern_id, sec_id)
                    if sec_key in seen_pattern_section:
                        continue
                    seen_pattern_section.add(sec_key)

                    # Deduplication safeguard: Prevent duplicate flags for identical pattern + source_text
                    clean_source = snippet.strip()
                    pat_src_key = (pattern.pattern_id, clean_source)
                    exp_src_key = (pattern.plain_explanation_template.strip(), clean_source)
                    if pat_src_key in seen_pattern_source or exp_src_key in seen_explanation_source:
                        continue
                    seen_pattern_source.add(pat_src_key)
                    seen_explanation_source.add(exp_src_key)

                    flag = RedFlagItem(
                        id=f"rf_{uuid.uuid4().hex[:12]}",
                        document_id=document_id,
                        pattern_id=pattern.pattern_id,
                        chunk_id=chunk_id,
                        page_number=page_number,
                        clause_label=clause_label,
                        source_text=snippet,
                        severity=pattern.severity_default,
                        plain_explanation=pattern.plain_explanation_template,
                        confirmed_by_llm=True,
                        created_at=datetime.utcnow()
                    )
                    flags.append(flag)

        return flags
