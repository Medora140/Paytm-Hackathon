from fastapi import APIRouter, Query, status
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ConfidenceScoreResponse,
    DocumentSummaryResponse,
    RedFlagsResponse,
)
from app.ml.service import ml_service

router = APIRouter(prefix="/documents/{id}", tags=["ML Analysis Service"])


@router.get("/summary", response_model=DocumentSummaryResponse, status_code=status.HTTP_200_OK)
async def get_document_summary(id: str, language: str = Query("en", description="Output language (en or hi)")) -> DocumentSummaryResponse:
    """
    Get plain-language structured summary for the specified document.
    Powered by Gemini with document-type specific tuning.
    """
    return ml_service.get_summary(document_id=id, language=language)


@router.get("/red-flags", response_model=RedFlagsResponse, status_code=status.HTTP_200_OK)
async def get_document_red_flags(id: str) -> RedFlagsResponse:
    """
    Get list of detected dispute-prone clauses and red flags with page citations
    scanned using the Rule-Based Red-Flag Knowledge Base.
    """
    return ml_service.get_red_flags(document_id=id)


@router.get("/confidence-score", response_model=ConfidenceScoreResponse, status_code=status.HTTP_200_OK)
async def get_confidence_score(id: str) -> ConfidenceScoreResponse:
    """
    Get transparent fairness and confidence score with itemized point deductions
    using the transparent weighted formula from §3.
    """
    return ml_service.get_confidence_score(document_id=id)


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_with_document(id: str, payload: ChatRequest) -> ChatResponse:
    """
    RAG conversational Q&A over the uploaded document with exact chunk citations
    and strict refusal guardrails against out-of-scope queries.
    """
    return ml_service.chat_with_document(document_id=id, payload=payload)

