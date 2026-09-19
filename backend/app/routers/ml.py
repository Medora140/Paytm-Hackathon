from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.auth import get_current_user
from app.ingestion.repository import repository
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ConfidenceScoreResponse,
    DocumentSummaryResponse,
    RedFlagsResponse,
)
from app.ml.service import ml_service
from app.validation import is_valid_uuid

router = APIRouter(prefix="/documents/{id}", tags=["ML Analysis Service"])


def _verify_document_ownership(document_id: str, user_id: str):
    if not is_valid_uuid(document_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )
    doc = repository.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )
    if doc.get("user_id") and doc.get("user_id") != user_id:
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
    Verified to ensure the document belongs to the authenticated user.
    """
    _verify_document_ownership(id, current_user["id"])
    return ml_service.get_summary(document_id=id, language=language)


@router.get("/red-flags", response_model=RedFlagsResponse, status_code=status.HTTP_200_OK)
async def get_document_red_flags(
    id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> RedFlagsResponse:
    """
    Get list of detected dispute-prone clauses and red flags with page citations.
    Verified to ensure the document belongs to the authenticated user.
    """
    _verify_document_ownership(id, current_user["id"])
    return ml_service.get_red_flags(document_id=id)


@router.get("/confidence-score", response_model=ConfidenceScoreResponse, status_code=status.HTTP_200_OK)
async def get_confidence_score(
    id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ConfidenceScoreResponse:
    """
    Get transparent fairness and confidence score with itemized point deductions.
    Verified to ensure the document belongs to the authenticated user.
    """
    _verify_document_ownership(id, current_user["id"])
    return ml_service.get_confidence_score(document_id=id)


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_with_document(
    id: str,
    payload: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ChatResponse:
    """
    RAG conversational Q&A over the uploaded document with exact chunk citations.
    Verified to ensure the document belongs to the authenticated user.
    """
    _verify_document_ownership(id, current_user["id"])
    return ml_service.chat_with_document(document_id=id, payload=payload, user_id=current_user["id"])

