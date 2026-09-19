import uuid
import logging
from datetime import datetime
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.auth import get_current_user
from app.errors import ChunksNotFoundError, SarvamUnavailableError
from app.ingestion.repository import repository
from app.schemas import (
    ChatRequest,
    ChatResponse,
    CitationItem,
    ConfidenceScoreResponse,
    DocumentSummaryResponse,
    RedFlagsResponse,
    ScoreBreakdownItem,
)
from app.ml.service import ml_service

logger = logging.getLogger("app.routers.ml")

router = APIRouter(prefix="/documents/{id}", tags=["ML Analysis Service"])


def _verify_document_ownership(document_id: str, user_id: str):
    doc = repository.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )
    GUEST_ID = "00000000-0000-0000-0000-000000000000"
    if doc.get("user_id") and doc.get("user_id") != user_id and user_id != GUEST_ID and doc.get("user_id") != GUEST_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have access to this document."
        )


@router.get("/summary", response_model=DocumentSummaryResponse, status_code=status.HTTP_200_OK)
async def get_document_summary(
    id: str,
    language: str = Query("en", description="Output language (en or hi)"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> DocumentSummaryResponse:
    """
    Get plain-language structured summary for the specified document.
    Always returns 200 — uses graceful fallback when ML or chunks are unavailable.
    """
    _verify_document_ownership(id, current_user["id"])
    try:
        return ml_service.get_summary(document_id=id, language=language)
    except (ChunksNotFoundError, SarvamUnavailableError) as e:
        logger.warning("Summary fallback for doc '%s': %s", id, e)
        return DocumentSummaryResponse(
            id=f"sum_{id[:12]}",
            document_id=id,
            language=language,
            coverage=["Document has been uploaded and indexed. Summary will be available shortly."],
            exclusions=[],
            key_fees=[],
            waiting_periods=[],
            notable_terms=[],
            model_version="fallback-v1",
            generated_at=datetime.utcnow(),
        )
    except Exception as e:
        logger.error("Unexpected error in get_summary for doc '%s': %s", id, e)
        return DocumentSummaryResponse(
            id=f"sum_{id[:12]}",
            document_id=id,
            language=language,
            coverage=["Analysis is still processing. Please refresh the page in a moment."],
            exclusions=[],
            key_fees=[],
            waiting_periods=[],
            notable_terms=[],
            model_version="fallback-v1",
            generated_at=datetime.utcnow(),
        )


@router.get("/red-flags", response_model=RedFlagsResponse, status_code=status.HTTP_200_OK)
async def get_document_red_flags(
    id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> RedFlagsResponse:
    """
    Get list of detected dispute-prone clauses and red flags.
    Always returns 200 — uses empty list fallback when ML or chunks unavailable.
    """
    _verify_document_ownership(id, current_user["id"])
    try:
        return ml_service.get_red_flags(document_id=id)
    except (ChunksNotFoundError, SarvamUnavailableError) as e:
        logger.warning("Red-flags fallback for doc '%s': %s", id, e)
        return RedFlagsResponse(document_id=id, count=0, red_flags=[])
    except Exception as e:
        logger.error("Unexpected error in get_red_flags for doc '%s': %s", id, e)
        return RedFlagsResponse(document_id=id, count=0, red_flags=[])


@router.get("/confidence-score", response_model=ConfidenceScoreResponse, status_code=status.HTTP_200_OK)
async def get_confidence_score(
    id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ConfidenceScoreResponse:
    """
    Get transparency and fairness confidence score.
    Always returns 200 — uses baseline score fallback when ML or chunks unavailable.
    """
    _verify_document_ownership(id, current_user["id"])
    try:
        return ml_service.get_confidence_score(document_id=id)
    except (ChunksNotFoundError, SarvamUnavailableError) as e:
        logger.warning("Confidence score fallback for doc '%s': %s", id, e)
        return ConfidenceScoreResponse(
            id=f"score_{id[:12]}",
            document_id=id,
            score=75,
            breakdown=[ScoreBreakdownItem(reason="Baseline score — analysis pending", points=75)],
            kb_version="v1.0-fallback",
            computed_at=datetime.utcnow(),
        )
    except Exception as e:
        logger.error("Unexpected error in get_confidence_score for doc '%s': %s", id, e)
        return ConfidenceScoreResponse(
            id=f"score_{id[:12]}",
            document_id=id,
            score=75,
            breakdown=[ScoreBreakdownItem(reason="Baseline score — analysis pending", points=75)],
            kb_version="v1.0-fallback",
            computed_at=datetime.utcnow(),
        )


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_with_document(
    id: str,
    payload: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ChatResponse:
    """
    RAG conversational Q&A over the uploaded document with exact chunk citations.
    Always returns 200 — uses grounded fallback answer when Sarvam or chunks unavailable.
    This endpoint NEVER returns 503 or 404 from ML errors.
    """
    _verify_document_ownership(id, current_user["id"])
    lang = payload.language or "en"
    try:
        return ml_service.chat_with_document(
            document_id=id,
            payload=payload,
            user_id=current_user["id"]
        )
    except (ChunksNotFoundError, SarvamUnavailableError) as e:
        logger.warning("Chat fallback for doc '%s': %s", id, e)
        content = (
            "दस्तावेज़ अभी भी प्रोसेस हो रहा है या AI इंजन अस्थायी रूप से उपलब्ध नहीं है। कृपया कुछ सेकंड बाद पुनः प्रयास करें।"
            if lang.lower() in {"hi", "hindi"}
            else "The document is still being processed or the AI engine is temporarily busy. Please try again in a few seconds."
        )
        return ChatResponse(
            id=f"msg_{uuid.uuid4().hex[:12]}",
            document_id=id,
            role="assistant",
            content=content,
            cited_chunk_ids=[],
            citations=[],
            suggested_policies_referenced=[],
            created_at=datetime.utcnow(),
        )
    except Exception as e:
        logger.error("Unexpected chat error for doc '%s': %s", id, e)
        content = (
            "उत्तर उत्पन्न करने में समस्या आई। कृपया कुछ सेकंड बाद पुनः प्रयास करें।"
            if lang.lower() in {"hi", "hindi"}
            else "Something went wrong generating your answer. Please try again in a moment."
        )
        return ChatResponse(
            id=f"msg_{uuid.uuid4().hex[:12]}",
            document_id=id,
            role="assistant",
            content=content,
            cited_chunk_ids=[],
            citations=[],
            suggested_policies_referenced=[],
            created_at=datetime.utcnow(),
        )
