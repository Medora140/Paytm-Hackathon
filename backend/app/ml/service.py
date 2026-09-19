import logging
from typing import Any, Dict, List, Optional, Tuple
from app.errors import SarvamUnavailableError
from app.ingestion.repository import repository as doc_repository
from app.ml.confidence_score import calculate_confidence_score
from app.ml.knowledge_base import RedFlagKnowledgeBase
from app.ml.chunk_resolver import get_chunks_for_document
from app.ml.rag_chat import GroundedRAGChat
from app.ml.red_flag_detector import RuleBasedRedFlagDetector
from app.ml.repository import ml_repository
from app.ml.summary_generator import (
    generate_fallback_summary,
    generate_plain_language_summary,
)
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ConfidenceScoreResponse,
    DocumentSummaryResponse,
    RedFlagsResponse,
)
from app.scraping.service import BenchmarkService

logger = logging.getLogger("app.ml.service")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


class MLService:
    """
    ML Analysis Service orchestrating document summarization,
    rule-based red flag detection, confidence scoring, and grounded RAG Q&A.
    Persists computed results via MLRepository (Supabase-first) and
    leverages caching for idempotency to avoid redundant LLM calls.
    """

    def __init__(self):
        self.kb = RedFlagKnowledgeBase()
        self.detector = RuleBasedRedFlagDetector(self.kb)
        self.chat_engine = GroundedRAGChat()
        self.benchmark_service = BenchmarkService()

    def get_summary(
        self,
        document_id: str,
        language: str = "en",
        chunks: Optional[List[Dict[str, Any]]] = None
    ) -> DocumentSummaryResponse:
        """
        Retrieves cached summary or generates a new plain-language structured summary,
        persisting the result in Supabase document_summaries for idempotency.
        """
        # 1. Idempotency check: Return cached summary from repository if available
        cached = ml_repository.get_summary(document_id=document_id, language=language)
        if cached is not None:
            logger.info("Serving cached summary for doc '%s' (lang=%s)", document_id, language)
            return cached

        # 2. Compute a source-grounded summary through Sarvam when available,
        # otherwise use the deterministic local fallback for analysis continuity.
        doc_chunks = chunks or get_chunks_for_document(document_id)
        try:
            summary = generate_plain_language_summary(
                document_id=document_id,
                chunks=doc_chunks,
                language=language
            )
        except SarvamUnavailableError:
            logger.warning("Sarvam unavailable for summary generation on doc '%s'; using local fallback summary.", document_id)
            summary = generate_fallback_summary(
                document_id=document_id,
                chunks=doc_chunks,
                language=language
            )

        # 3. Persist generated summary to Supabase
        ml_repository.save_summary(summary)
        return summary

    def get_red_flags(
        self,
        document_id: str,
        chunks: Optional[List[Dict[str, Any]]] = None
    ) -> RedFlagsResponse:
        """
        Retrieves cached red flags or scans document chunks for high-risk clauses,
        persisting the results in Supabase red_flags table.
        """
        # 1. Idempotency check: Return cached red flags if previously stored
        cached_flags = ml_repository.get_red_flags(document_id=document_id)
        if cached_flags is not None:
            logger.info("Serving %d cached red flags for doc '%s'", len(cached_flags), document_id)
            return RedFlagsResponse(
                document_id=document_id,
                count=len(cached_flags),
                red_flags=cached_flags
            )

        # 2. Detect red flags against Knowledge Base
        doc_chunks = chunks or get_chunks_for_document(document_id)
        flags = self.detector.detect_red_flags(document_id, doc_chunks)

        # 3. Persist detected flags to Supabase
        ml_repository.save_red_flags(document_id=document_id, flags=flags)

        return RedFlagsResponse(
            document_id=document_id,
            count=len(flags),
            red_flags=flags
        )

    def _derive_benchmark_penalty(
        self,
        document_id: str
    ) -> int:
        """
        Derives benchmark penalty points by comparing document category/attributes
        against median market comparables from BenchmarkService.
        
        Rules:
        - Health Insurance:
          - Room Rent Cap: 5 points off if stricter than comparables
          - PED Waiting Period > 24 months: 4 points off
          - Mandatory Co-pay > 0%: 3 points off
        - Mutual Fund:
          - High Regular Expense Ratio (> 1.60%): 3 points off
          - Strict Exit Load (> 180 days lock-in): 3 points off
        Capped at 15 points total.
        """
        try:
            # Query document metadata for category and issuer
            doc_meta = doc_repository.get_document(document_id)
            category = "health_insurance"
            issuer_name = None
            if doc_meta:
                raw_type = doc_meta.get("document_type")
                category = raw_type.value if hasattr(raw_type, "value") else str(raw_type or "health_insurance")
                issuer_name = doc_meta.get("issuer_name")

            # Call BenchmarkService
            comp_res = self.benchmark_service.get_comparisons_for_document(
                document_id=document_id,
                category=category,
                issuer_name=issuer_name
            )

            penalty = 0
            target_attrs = comp_res.target_attributes or {}

            if category == "health_insurance":
                # Check room rent cap
                room_rent = str(target_attrs.get("room_rent_cap", "")).lower()
                if "1%" in room_rent or "5,000" in room_rent or "sub-limit" in room_rent:
                    penalty += 5

                # Check pre-existing waiting period
                ped = str(target_attrs.get("waiting_period_pre_existing", "")).lower()
                if any(m in ped for m in ["36 months", "48 months", "3 years", "4 years"]):
                    penalty += 4

                # Check co-pay
                copay = str(target_attrs.get("co_pay_percent", "")).lower()
                if any(c in copay for c in ["10%", "20%", "co-pay"]):
                    penalty += 3

            elif category == "mutual_fund":
                # Check regular expense ratio vs benchmark median (~1.55%)
                ter = str(target_attrs.get("expense_ratio_regular", "")).replace("%", "")
                try:
                    if float(ter) > 1.60:
                        penalty += 3
                except ValueError:
                    pass

                # Check exit load
                exit_load = str(target_attrs.get("exit_load", "")).lower()
                if "365 days" in exit_load or "1 year" in exit_load:
                    penalty += 3

            clamped_penalty = min(penalty, 15)
            logger.info(
                "Derived benchmark_penalty=%d for doc '%s' (category=%s, issuer=%s)",
                clamped_penalty,
                document_id,
                category,
                issuer_name
            )
            return clamped_penalty

        except Exception as e:
            logger.warning("Failed to derive benchmark penalty for doc '%s': %s", document_id, e)
            return 0

    def get_confidence_score(
        self,
        document_id: str,
        chunks: Optional[List[Dict[str, Any]]] = None,
        benchmark_penalty: Optional[int] = None,
        transparency_bonus: int = 2
    ) -> ConfidenceScoreResponse:
        """
        Calculates transparency & fairness confidence score from red flags and
        live benchmark comparison penalties, persisting the result to Supabase.
        """
        # 1. Idempotency check: Return cached confidence score if already computed
        cached_score = ml_repository.get_confidence_score(document_id=document_id)
        if cached_score is not None:
            logger.info("Serving cached confidence_score (%d/100) for doc '%s'", cached_score.score, document_id)
            return cached_score

        # 2. Derive benchmark penalty if not explicitly passed
        effective_penalty = (
            benchmark_penalty
            if benchmark_penalty is not None
            else self._derive_benchmark_penalty(document_id)
        )

        # 3. Detect or retrieve flags
        doc_chunks = chunks or get_chunks_for_document(document_id)
        flags = self.detector.detect_red_flags(document_id, doc_chunks)

        # 4. Calculate score with itemized breakdown
        score = calculate_confidence_score(
            document_id=document_id,
            red_flags=flags,
            benchmark_penalty=effective_penalty,
            transparency_bonus=transparency_bonus
        )

        # 5. Persist confidence score in Supabase
        ml_repository.save_confidence_score(score)
        return score

    def chat_with_document(
        self,
        document_id: str,
        payload: ChatRequest,
        chunks: Optional[List[Dict[str, Any]]] = None,
        user_id: Optional[str] = None
    ) -> ChatResponse:
        """
        Conversational grounded RAG Q&A with dual-context (document chunks + market benchmarks).
        Persists both the user question and assistant response into chat_messages.
        """
        if not user_id:
            raise ValueError("A verified user_id is required to save chat messages.")
        effective_user_id = user_id

        # 1. Persist user message to Supabase
        ml_repository.save_chat_message(
            document_id=document_id,
            user_id=effective_user_id,
            role="user",
            content=payload.question
        )

        # 2. Fetch benchmark data if requested or available
        benchmark_data = None
        if payload.include_benchmarks:
            try:
                doc_meta = doc_repository.get_document(document_id)
                cat = "health_insurance"
                iss = None
                if doc_meta:
                    raw_type = doc_meta.get("document_type")
                    cat = raw_type.value if hasattr(raw_type, "value") else str(raw_type or "health_insurance")
                    iss = doc_meta.get("issuer_name")
                benchmark_data = self.benchmark_service.get_comparisons_for_document(
                    document_id=document_id,
                    category=cat,
                    issuer_name=iss
                )
            except Exception as e:
                logger.warning("Failed to attach benchmark data for chat on doc '%s': %s", document_id, e)

        # 3. Generate grounded RAG answer
        doc_chunks = chunks or get_chunks_for_document(document_id)
        response = self.chat_engine.chat(
            document_id=document_id,
            question=payload.question,
            chunks=doc_chunks,
            language=payload.language or "en",
            benchmark_data=benchmark_data
        )

        # 4. Persist assistant response to Supabase
        ml_repository.save_chat_message(
            document_id=document_id,
            user_id=effective_user_id,
            role="assistant",
            content=response.content,
            cited_chunk_ids=response.cited_chunk_ids
        )

        return response


# Global singleton instance
ml_service = MLService()
