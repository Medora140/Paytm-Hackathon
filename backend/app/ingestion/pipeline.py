import uuid
import logging
from typing import Any, Dict, Optional
from app.identity import DEMO_USER_ID
from app.schemas import DocumentStatus, DocumentType
from app.ingestion.storage import StorageManager
from app.ingestion.detector import PDFTypeDetector
from app.ingestion.extractor import PDFTextExtractor
from app.ingestion.chunker import ClauseChunker
from app.ingestion.embedder import ChunkEmbedder
from app.ingestion.repository import DocumentRepository, repository

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    End-to-end document ingestion orchestrator:
    1. Upload & store raw file in object storage (status: uploaded)
    2. Detect text-native vs. scanned PDF
    3. Extract text (pypdf/pdfplumber or Tesseract OCR fallback) (status: extracted)
    4. Clause-level chunking with page number preservation (status: chunked)
    5. Generate 384-dimensional chunk embeddings (status: embedded)
    6. Persist to document_chunks table / repository
    """

    def __init__(
        self,
        storage_mgr: Optional[StorageManager] = None,
        detector: Optional[PDFTypeDetector] = None,
        extractor: Optional[PDFTextExtractor] = None,
        chunker: Optional[ClauseChunker] = None,
        embedder: Optional[ChunkEmbedder] = None,
        repo: Optional[DocumentRepository] = None,
    ):
        self.storage_mgr = storage_mgr or StorageManager()
        self.detector = detector or PDFTypeDetector()
        self.extractor = extractor or PDFTextExtractor()
        self.chunker = chunker or ClauseChunker()
        self.embedder = embedder or ChunkEmbedder()
        self.repository = repo or repository

    def detect_issuer(self, filename: str, pages_data: list) -> Optional[str]:
        """Heuristic issuer detector based on filename and header text."""
        combined_header = filename.lower()
        if pages_data:
            combined_header += " " + pages_data[0].get("text", "")[:500].lower()

        if "hdfc" in combined_header:
            return "HDFC Asset Management Company Limited"
        elif "sbi" in combined_header:
            return "SBI Mutual Fund / State Bank of India"
        elif "star health" in combined_header:
            return "Star Health & Allied Insurance"
        elif "icici" in combined_header:
            return "ICICI Prudential"
        elif "axis" in combined_header:
            return "Axis Bank / Axis Mutual Fund"
        return None

    def process_document(
        self,
        file_bytes: Optional[bytes] = None,
        filename: Optional[str] = None,
        document_type: DocumentType = DocumentType.HEALTH_INSURANCE,
        user_id: str = DEMO_USER_ID,
        doc_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the complete document ingestion pipeline synchronously.
        Implements explicit re-submission and idempotency semantics:
        1. If document already exists AND has chunks AND is fully analyzed/embedded:
           returns the existing document status/result without redundant recomputation.
        2. If document exists but has 0 chunks (previously failed/aborted run):
           resumes ingestion (extraction -> chunking -> embedding -> ML) for that exact doc_id.
        """
        doc_id = doc_id or str(uuid.uuid4())

        try:
            # Check re-submission semantics
            existing_doc = self.repository.get_document(doc_id)
            if existing_doc:
                existing_chunks = self.repository.get_chunks(doc_id)
                # Semantics 1: Already processed with chunks and analyzed/embedded
                if existing_chunks and len(existing_chunks) > 0 and existing_doc.get("status") in (
                    DocumentStatus.ANALYZED,
                    DocumentStatus.EMBEDDED,
                ):
                    logger.info(
                        "[%s] Document already exists with %d chunks and status '%s'. Returning existing status (idempotent).",
                        doc_id,
                        len(existing_chunks),
                        existing_doc.get("status")
                    )
                    return {
                        "document_id": doc_id,
                        "status": existing_doc.get("status"),
                        "storage_path": existing_doc.get("storage_path"),
                        "pages_count": None,
                        "chunks_count": len(existing_chunks),
                        "issuer_name": existing_doc.get("issuer_name")
                    }

                # Semantics 2: Exists but has 0 chunks (resuming failed/incomplete run)
                logger.info("[%s] Resuming ingestion for existing document (current status: %s, chunks: 0)...",
                            doc_id, existing_doc.get("status"))
                if (not file_bytes or len(file_bytes) == 0) and existing_doc.get("storage_path"):
                    logger.info("[%s] Retrieving raw document bytes from storage path: %s", doc_id, existing_doc.get("storage_path"))
                    file_bytes = self.storage_mgr.retrieve_file(existing_doc.get("storage_path"))
                if not filename and existing_doc.get("filename"):
                    filename = existing_doc.get("filename")
                if existing_doc.get("document_type"):
                    document_type = existing_doc.get("document_type")
                if existing_doc.get("user_id"):
                    user_id = existing_doc.get("user_id")

            if not file_bytes:
                raise ValueError(f"Cannot process document '{doc_id}': no file bytes provided and none found in storage.")

            filename = filename or (existing_doc.get("filename") if existing_doc else "uploaded_document.pdf")

            # Stage 1: Store raw file in object storage
            logger.info("[%s] Stage 1: Uploading raw file to storage...", doc_id)
            storage_path = self.storage_mgr.store_file(doc_id, filename, file_bytes)

            self.repository.create_document(
                doc_id=doc_id,
                user_id=user_id,
                filename=filename,
                document_type=document_type,
                storage_path=storage_path
            )
            self.repository.clear_chunks(doc_id)

            # Stage 2 & 3: Detect and Extract
            logger.info("[%s] Stage 2 & 3: Extracting text (native / OCR)...", doc_id)
            self.repository.update_status(
                doc_id=doc_id,
                status=DocumentStatus.UPLOADED,
                pipeline_stage="Extracting document text..."
            )

            pages_data = self.extractor.extract(file_bytes)
            issuer_name = self.detect_issuer(filename, pages_data)

            self.repository.update_status(
                doc_id=doc_id,
                status=DocumentStatus.EXTRACTED,
                pipeline_stage=f"Extracted {len(pages_data)} pages",
                issuer_name=issuer_name
            )

            # Stage 4: Clause-level chunking
            logger.info("[%s] Stage 4: Segmenting into clause chunks...", doc_id)
            self.repository.update_status(
                doc_id=doc_id,
                status=DocumentStatus.EXTRACTED,
                pipeline_stage="Segmenting document clauses..."
            )

            raw_chunks = self.chunker.chunk_pages(pages_data)

            self.repository.update_status(
                doc_id=doc_id,
                status=DocumentStatus.CHUNKED,
                pipeline_stage=f"Chunked into {len(raw_chunks)} clauses"
            )

            # Stage 5: Embeddings
            import time
            t_emb_start = time.time()
            logger.info("[%s] Stage 5: Computing embeddings for %s chunks...", doc_id, len(raw_chunks))
            self.repository.update_status(
                doc_id=doc_id,
                status=DocumentStatus.CHUNKED,
                pipeline_stage=f"Generating embeddings for {len(raw_chunks)} clauses..."
            )

            embedded_chunks = self.embedder.embed_chunks(raw_chunks)
            emb_duration = time.time() - t_emb_start
            logger.info("[%s] Stage 5 COMPLETE: Computed embeddings for %d chunks in %.2fs", doc_id, len(embedded_chunks), emb_duration)

            # Stage 6: Write to document_chunks
            t_persist_start = time.time()
            logger.info("[%s] Stage 6: Persisting %s embedded chunks to database...", doc_id, len(embedded_chunks))
            saved_count = self.repository.save_chunks(doc_id, embedded_chunks)
            persist_duration = time.time() - t_persist_start
            logger.info("[%s] Stage 6 COMPLETE: Persisted %d chunks to Supabase in %.2fs", doc_id, saved_count, persist_duration)

            # Stage 7: Trigger ML Analysis (Red flags, Confidence score) -> ANALYZED
            self.repository.update_status(
                doc_id=doc_id,
                status=DocumentStatus.EMBEDDED,
                pipeline_stage="Auditing policy clauses, detecting red flags & calculating fairness score..."
            )
            analysis_summary = f"Ingestion complete: {saved_count} clauses embedded and indexed"
            final_status = DocumentStatus.EMBEDDED
            try:
                from app.ml.service import ml_service
                logger.info("[%s] Stage 7: Triggering ML analysis...", doc_id)
                flags_resp = ml_service.get_red_flags(doc_id, chunks=embedded_chunks)
                conf_resp = ml_service.get_confidence_score(doc_id, chunks=embedded_chunks)
                final_status = DocumentStatus.ANALYZED
                analysis_summary = (
                    f"Analysis complete: {flags_resp.count} red flags identified | "
                    f"Fairness score {conf_resp.score}/100"
                )
            except Exception as ml_err:
                logger.warning("[%s] ML analysis deferred or failed: %s", doc_id, ml_err)

            self.repository.update_status(
                doc_id=doc_id,
                status=final_status,
                pipeline_stage=analysis_summary,
                issuer_name=issuer_name
            )

            return {
                "document_id": doc_id,
                "status": final_status,
                "storage_path": storage_path,
                "pages_count": len(pages_data),
                "chunks_count": saved_count,
                "issuer_name": issuer_name
            }

        except Exception as e:
            logger.exception("[%s] Ingestion pipeline failed: %s", doc_id, e)
            self.repository.update_status(
                doc_id=doc_id,
                status=DocumentStatus.FAILED,
                pipeline_stage=f"Failed: {str(e)}"
            )
            raise e


# Global pipeline instance
default_pipeline = IngestionPipeline()


def get_ingestion_pipeline() -> IngestionPipeline:
    return default_pipeline
