import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile, status
from app.schemas import (
    DocumentDeleteResponse,
    DocumentDetailResponse,
    DocumentListItem,
    DocumentStatus,
    DocumentType,
    DocumentUploadResponse,
)
from app.identity import DEMO_USER_ID
from app.ingestion.repository import repository
from app.ingestion.pipeline import get_ingestion_pipeline

router = APIRouter(prefix="/documents", tags=["Ingestion Service"])


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Uploaded policy PDF or document file"),
    document_type: Optional[DocumentType] = Form(DocumentType.HEALTH_INSURANCE, description="Category of document")
) -> DocumentUploadResponse:
    """
    Upload a new financial document (multipart/form-data).
    Stores raw file in object storage and initiates the ingestion pipeline:
    detect text-native vs scanned -> extraction -> clause chunking -> embedding.
    """
    file_bytes = await file.read()
    filename = file.filename or "uploaded_document.pdf"
    doc_id = str(uuid.uuid4())
    doc_type = document_type or DocumentType.HEALTH_INSURANCE
    user_id = DEMO_USER_ID

    pipeline = get_ingestion_pipeline()
    storage_path = pipeline.storage_mgr.store_file(doc_id, filename, file_bytes)

    doc_record = repository.create_document(
        doc_id=doc_id,
        user_id=user_id,
        filename=filename,
        document_type=doc_type,
        storage_path=storage_path
    )

    # Schedule complete pipeline processing in background
    background_tasks.add_task(
        pipeline.process_document,
        file_bytes=file_bytes,
        filename=filename,
        document_type=doc_type,
        user_id=user_id,
        doc_id=doc_id
    )

    return DocumentUploadResponse(
        id=doc_id,
        filename=filename,
        document_type=doc_type,
        status=DocumentStatus.UPLOADED,
        storage_path=storage_path,
        uploaded_at=doc_record["uploaded_at"]
    )


@router.get("", response_model=List[DocumentListItem], status_code=status.HTTP_200_OK)
async def list_documents() -> List[DocumentListItem]:
    """
    List all documents uploaded by current user.
    """
    docs = repository.list_documents()
    items = []
    for d in docs:
        items.append(
            DocumentListItem(
                id=d["id"],
                user_id=d.get("user_id", DEMO_USER_ID),
                filename=d["filename"],
                document_type=DocumentType(d.get("document_type", "health_insurance")),
                status=DocumentStatus(d.get("status", "uploaded")),
                issuer_name=d.get("issuer_name"),
                uploaded_at=d.get("uploaded_at", datetime.utcnow()),
                confidence_score=d.get("confidence_score")
            )
        )
    return items


@router.get("/{id}", response_model=DocumentDetailResponse, status_code=status.HTTP_200_OK)
async def get_document_metadata_and_status(id: str) -> DocumentDetailResponse:
    """
    Get document metadata and live processing status / pipeline stage.
    """
    doc = repository.get_document(id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{id}' not found."
        )

    return DocumentDetailResponse(
        id=doc["id"],
        user_id=doc.get("user_id", DEMO_USER_ID),
        filename=doc["filename"],
        document_type=DocumentType(doc.get("document_type", "health_insurance")),
        storage_path=doc["storage_path"],
        status=DocumentStatus(doc.get("status", "uploaded")),
        pipeline_stage=doc.get("pipeline_stage", "Processing"),
        issuer_name=doc.get("issuer_name"),
        uploaded_at=doc.get("uploaded_at", datetime.utcnow()),
        deleted_at=doc.get("deleted_at")
    )


@router.delete("/{id}", response_model=DocumentDeleteResponse, status_code=status.HTTP_200_OK)
async def delete_document(id: str) -> DocumentDeleteResponse:
    """
    Delete document + cascade erase associated chunks, summaries, flags, chat history
    in compliance with DPDP Act 2023 ("right to erasure").
    """
    repository.delete_document(id)
    return DocumentDeleteResponse(
        status="deleted",
        document_id=id,
        message="Document and associated data permanently deleted (DPDP right to erasure)."
    )
