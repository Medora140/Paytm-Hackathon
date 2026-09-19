import uuid
import logging
from typing import Any, Dict, Optional
from app.schemas import DocumentStatus, DocumentType
from app.ingestion.storage import StorageManager
from app.ingestion.detector import PDFTypeDetector
from app.ingestion.extractor import PDFTextExtractor
from app.ingestion.chunker import ClauseChunker
from app.ingestion.embedder import ChunkEmbedder
from app.ingestion.repository import DocumentRepository, repository
from app.ingestion.classifier import classifier

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    End-to-end document ingestion orchestrator:
    1. Upload & store raw file in object storage (status: uploaded)
    2. Detect text-native vs. scanned PDF
    3. Extract text (pypdf/fitz or Tesseract OCR fallback) (status: extracted)
    4. Automatically identify document type & issuer with AI classifier
    5. Clause-level chunking with page number preservation (status: chunked)
    6. Generate 384-dimensional chunk embeddings (status: embedded)
    7. Persist to document_chunks table / repository
    8. Run red-flags and fairness score analysis (status: analyzed)
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
            return "HDFC Asset Management / HDFC ERGO"
        elif "sbi" in combined_header:
            return "SBI Mutual Fund / State Bank of India"
        elif "star health" in combined_header:
            return "Star Health & Allied Insurance"
        elif "care" in combined_header:
            return "Care Health Insurance"
        elif "niva" in combined_header or "bupa" in combined_header:
            return "Niva Bupa Health Insurance"
        elif "icici" in combined_header:
            return "ICICI Prudential / Lombard"
        elif "axis" in combined_header:
            return "Axis Bank / Axis Mutual Fund"
        return None

    def process_document(
        self,
        file_bytes: bytes,
        filename: str,
        document_type: DocumentType = DocumentType.HEALTH_INSURANCE,
        user_id: Optional[str] = None,
        doc_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the complete document ingestion pipeline synchronously.
        """
        doc_id = doc_id or str(uuid.uuid4())
        user_id = user_id or "00000000-0000-0000-0000-000000000000"

        try:
            # Stage 1: Store raw file in object storage
            logger.info("[%s] Stage 1: Uploading raw file to storage...", doc_id)
            storage_path = self.storage_mgr.store_file(doc_id, filename, file_bytes)

            # The upload route already creates the document row; the background
            # pipeline must only update that row as it progresses, never insert it a second time.

            # Stage 2 & 3: Detect and Extract
            logger.info("[%s] Stage 2 & 3: Extracting text (native / OCR)...", doc_id)
            self.repository.update_status(
                doc_id=doc_id,
                status=DocumentStatus.UPLOADED,
                pipeline_stage="Extracting document text..."
            )

            pages_data = self.extractor.extract(file_bytes)

            # Automatic AI Document Classification
            detected_type, doc_lang, detected_issuer = classifier.classify_document(filename, pages_data)
            issuer_name = detected_issuer or self.detect_issuer(filename, pages_data)

            self.repository.update_status(
                doc_id=doc_id,
                status=DocumentStatus.EXTRACTED,
                pipeline_stage=f"AI identified: {detected_type.value.replace('_', ' ').title()} ({len(pages_data)} pages)",
                issuer_name=issuer_name,
                document_type=detected_type
            )

            # Stage 4: Clause-level chunking
            logger.info("[%s] Stage 4: Segmenting into clause chunks...", doc_id)
            self.repository.update_status(
                doc_id=doc_id,
                status=DocumentStatus.EXTRACTED,
                pipeline_stage="Segmenting document clauses..."
            )

            raw_chunks = self.chunker.chunk_pages(pages_data)

            # Safeguard against zero chunks on sparse documents
            if not raw_chunks and pages_data:
                for p in pages_data:
                    txt = (p.get("text") or "").strip()
                    if txt:
                        raw_chunks.append({
                            "page_number": p.get("page_number", 1),
                            "clause_label": f"Page {p.get('page_number', 1)} Content",
                            "text": txt
                        })
            if not raw_chunks:
                raw_chunks.append({
                    "page_number": 1,
                    "clause_label": "Document Overview",
                    "text": f"Document {filename} uploaded for analysis."
                })

            self.repository.update_status(
                doc_id=doc_id,
                status=DocumentStatus.CHUNKED,
                pipeline_stage=f"Chunked into {len(raw_chunks)} clauses"
            )

            # Stage 5: Embeddings
            logger.info("[%s] Stage 5: Computing embeddings for %s chunks...", doc_id, len(raw_chunks))
            self.repository.update_status(
                doc_id=doc_id,
                status=DocumentStatus.CHUNKED,
                pipeline_stage=f"Generating embeddings for {len(raw_chunks)} clauses..."
            )

            embedded_chunks = self.embedder.embed_chunks(raw_chunks)

            # Stage 6: Write to document_chunks
            logger.info("[%s] Stage 6: Persisting %s embedded chunks...", doc_id, len(embedded_chunks))
            saved_count = self.repository.save_chunks(doc_id, embedded_chunks)

            # Stage 7: Trigger ML Analysis (Red flags, Confidence score) -> ANALYZED
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
                issuer_name=issuer_name,
                document_type=detected_type
            )

            return {
                "document_id": doc_id,
                "status": final_status,
                "document_type": detected_type,
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
