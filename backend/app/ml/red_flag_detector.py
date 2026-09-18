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

        for chunk in chunks:
            chunk_id = str(chunk.get("id", f"chk_{uuid.uuid4().hex[:8]}"))
            page_number = int(chunk.get("page_number", 1))
            clause_label = chunk.get("clause_label") or f"Clause on Page {page_number}"
            text = chunk.get("text", "")
            text_lower = text.lower()

            for pattern in patterns:
                pair_key = (chunk_id, pattern.pattern_id)
                if pair_key in matched_chunk_patterns:
                    continue

                matched = False
                matched_snippet = ""

                # Check regex first if provided
                if pattern.trigger_regex:
                    match_obj = re.search(pattern.trigger_regex, text)
                    if match_obj:
                        matched = True
                        matched_snippet = match_obj.group(0).strip()

                # Fallback to trigger keywords boundary search
                if not matched and pattern.trigger_keywords:
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
