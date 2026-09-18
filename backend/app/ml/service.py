from typing import Any, Dict, List, Optional
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ConfidenceScoreResponse,
    DocumentSummaryResponse,
    RedFlagsResponse,
)
from app.ml.confidence_score import calculate_confidence_score
from app.ml.knowledge_base import RedFlagKnowledgeBase
from app.ml.mock_data import get_chunks_for_document
from app.ml.red_flag_detector import RuleBasedRedFlagDetector
from app.ml.summary_generator import generate_plain_language_summary
from app.ml.rag_chat import GroundedRAGChat


class MLService:
    """
    ML Analysis Service orchestrating document summarization,
    rule-based red flag detection, confidence scoring, and grounded RAG Q&A.
    """

    def __init__(self):
        self.kb = RedFlagKnowledgeBase()
        self.detector = RuleBasedRedFlagDetector(self.kb)
        self.chat_engine = GroundedRAGChat()

    def get_summary(
        self,
        document_id: str,
        language: str = "en",
        chunks: Optional[List[Dict[str, Any]]] = None
    ) -> DocumentSummaryResponse:
        """
        Generates or retrieves plain-language structured summary for document.
        """
        doc_chunks = chunks or get_chunks_for_document(document_id)
        return generate_plain_language_summary(
            document_id=document_id,
            chunks=doc_chunks,
            language=language
        )

    def get_red_flags(
        self,
        document_id: str,
        chunks: Optional[List[Dict[str, Any]]] = None
    ) -> RedFlagsResponse:
        """
        Scans document chunks for high-risk clauses and dispute red flags with citations.
        """
        doc_chunks = chunks or get_chunks_for_document(document_id)
        flags = self.detector.detect_red_flags(document_id, doc_chunks)
        return RedFlagsResponse(
            document_id=document_id,
            count=len(flags),
            red_flags=flags
        )

    def get_confidence_score(
        self,
        document_id: str,
        chunks: Optional[List[Dict[str, Any]]] = None,
        benchmark_penalty: int = 0,
        transparency_bonus: int = 2
    ) -> ConfidenceScoreResponse:
        """
        Calculates transparency & fairness confidence score from red flags using the §3 formula.
        """
        doc_chunks = chunks or get_chunks_for_document(document_id)
        flags = self.detector.detect_red_flags(document_id, doc_chunks)
        
        # Calculate score with transparent breakdown
        return calculate_confidence_score(
            document_id=document_id,
            red_flags=flags,
            benchmark_penalty=benchmark_penalty,
            transparency_bonus=transparency_bonus
        )

    def chat_with_document(
        self,
        document_id: str,
        payload: ChatRequest,
        chunks: Optional[List[Dict[str, Any]]] = None
    ) -> ChatResponse:
        """
        Conversational grounded RAG Q&A with strict document boundary guardrails.
        """
        doc_chunks = chunks or get_chunks_for_document(document_id)
        return self.chat_engine.chat(
            document_id=document_id,
            question=payload.question,
            chunks=doc_chunks,
            language=payload.language or "en"
        )


# Global singleton instance
ml_service = MLService()
