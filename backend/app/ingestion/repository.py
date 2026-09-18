import uuid
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional
from app.db import get_db
from app.schemas import DocumentStatus, DocumentType

logger = logging.getLogger(__name__)


class DocumentRepository:
    """
    Repository layer for documents and document_chunks tables.
    Persists data to Supabase PostgreSQL with local memory cache fallback
    to ensure full operational stability across test and development environments.
    """

    def __init__(self):
        # In-memory stores
        self._documents: Dict[str, Dict[str, Any]] = {}
        self._chunks: Dict[str, List[Dict[str, Any]]] = {}

    def create_document(
        self,
        doc_id: str,
        user_id: str,
        filename: str,
        document_type: DocumentType,
        storage_path: str,
        issuer_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a document row with initial status 'uploaded'.
        """
        now = datetime.utcnow()
        doc_data = {
            "id": doc_id,
            "user_id": user_id,
            "filename": filename,
            "document_type": document_type.value if hasattr(document_type, "value") else str(document_type),
            "storage_path": storage_path,
            "status": DocumentStatus.UPLOADED,
            "pipeline_stage": "File uploaded - Queued for processing",
            "issuer_name": issuer_name,
            "uploaded_at": now,
            "deleted_at": None,
            "confidence_score": None
        }

        # Save to memory cache
        self._documents[doc_id] = doc_data

        # Attempt writing to Supabase
        try:
            db = get_db()
            db.table("documents").insert({
                "id": doc_id,
                "user_id": user_id,
                "filename": filename,
                "document_type": doc_data["document_type"],
                "storage_path": storage_path,
                "status": DocumentStatus.UPLOADED.value,
                "issuer_name": issuer_name,
                "uploaded_at": now.isoformat()
            }).execute()
        except Exception as e:
            logger.debug("Supabase documents.insert fallback to in-memory: %s", e)

        return doc_data

    def update_status(
        self,
        doc_id: str,
        status: DocumentStatus,
        pipeline_stage: str,
        issuer_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Updates document status, pipeline stage description, and optional detected issuer name.
        """
        doc = self._documents.get(doc_id)
        if doc:
            doc["status"] = status
            doc["pipeline_stage"] = pipeline_stage
            if issuer_name:
                doc["issuer_name"] = issuer_name

        # Attempt writing to Supabase
        try:
            db = get_db()
            payload: Dict[str, Any] = {"status": status.value if hasattr(status, "value") else str(status)}
            if issuer_name:
                payload["issuer_name"] = issuer_name
            db.table("documents").update(payload).eq("id", doc_id).execute()
        except Exception as e:
            logger.debug("Supabase documents.update fallback to in-memory: %s", e)

        return doc

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves document metadata by ID.
        """
        # Try memory cache first
        if doc_id in self._documents:
            return self._documents[doc_id]

        # Try Supabase query
        try:
            db = get_db()
            res = db.table("documents").select("*").eq("id", doc_id).execute()
            if hasattr(res, "data") and res.data:
                item = res.data[0]
                doc = {
                    "id": item.get("id"),
                    "user_id": item.get("user_id"),
                    "filename": item.get("filename"),
                    "document_type": DocumentType(item.get("document_type", "health_insurance")),
                    "storage_path": item.get("storage_path"),
                    "status": DocumentStatus(item.get("status", "uploaded")),
                    "pipeline_stage": f"Status: {item.get('status')}",
                    "issuer_name": item.get("issuer_name"),
                    "uploaded_at": datetime.fromisoformat(item["uploaded_at"]) if "uploaded_at" in item else datetime.utcnow(),
                    "deleted_at": None,
                    "confidence_score": None
                }
                self._documents[doc_id] = doc
                return doc
        except Exception as e:
            logger.debug("Supabase documents.select failed: %s", e)

        return None

    def list_documents(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lists documents, optionally filtered by user_id.
        """
        docs = list(self._documents.values())
        if user_id:
            docs = [d for d in docs if d.get("user_id") == user_id]

        if not docs:
            # Check Supabase
            try:
                db = get_db()
                q = db.table("documents").select("*")
                if user_id:
                    q = q.eq("user_id", user_id)
                res = q.execute()
                if hasattr(res, "data") and res.data:
                    for item in res.data:
                        d_id = item.get("id")
                        doc = {
                            "id": d_id,
                            "user_id": item.get("user_id"),
                            "filename": item.get("filename"),
                            "document_type": DocumentType(item.get("document_type", "health_insurance")),
                            "storage_path": item.get("storage_path"),
                            "status": DocumentStatus(item.get("status", "uploaded")),
                            "pipeline_stage": f"Status: {item.get('status')}",
                            "issuer_name": item.get("issuer_name"),
                            "uploaded_at": datetime.fromisoformat(item["uploaded_at"]) if "uploaded_at" in item else datetime.utcnow(),
                            "confidence_score": None
                        }
                        self._documents[d_id] = doc
                    docs = list(self._documents.values())
            except Exception as e:
                logger.debug("Supabase documents.select all failed: %s", e)

        return docs

    def delete_document(self, doc_id: str) -> bool:
        """
        Deletes document and cascades removal of chunks (DPDP right to erasure).
        """
        self._documents.pop(doc_id, None)
        self._chunks.pop(doc_id, None)

        try:
            db = get_db()
            db.table("documents").delete().eq("id", doc_id).execute()
        except Exception as e:
            logger.debug("Supabase documents.delete error: %s", e)

        return True

    def save_chunks(self, doc_id: str, chunks: List[Dict[str, Any]]) -> int:
        """
        Saves document chunks with embeddings into document_chunks table / memory.
        """
        now = datetime.utcnow()
        chunk_records = []

        for c in chunks:
            chunk_id = c.get("id") or str(uuid.uuid4())
            rec = {
                "id": chunk_id,
                "document_id": doc_id,
                "page_number": c["page_number"],
                "clause_label": c.get("clause_label"),
                "text": c["text"],
                "embedding": c.get("embedding", []),
                "created_at": now
            }
            chunk_records.append(rec)

        self._chunks[doc_id] = chunk_records

        # Attempt persisting to Supabase document_chunks table
        try:
            db = get_db()
            supabase_rows = []
            for r in chunk_records:
                supabase_rows.append({
                    "id": r["id"],
                    "document_id": r["document_id"],
                    "page_number": r["page_number"],
                    "clause_label": r["clause_label"],
                    "text": r["text"],
                    "embedding": r["embedding"],
                    "created_at": now.isoformat()
                })
            # Insert in batches of 50
            for i in range(0, len(supabase_rows), 50):
                batch = supabase_rows[i : i + 50]
                db.table("document_chunks").insert(batch).execute()
        except Exception as e:
            logger.debug("Supabase document_chunks.insert fallback to in-memory: %s", e)

        return len(chunk_records)

    def get_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        Returns all chunks for a given document.
        """
        if doc_id in self._chunks:
            return self._chunks[doc_id]

        try:
            db = get_db()
            res = db.table("document_chunks").select("*").eq("document_id", doc_id).execute()
            if hasattr(res, "data") and res.data:
                self._chunks[doc_id] = res.data
                return res.data
        except Exception as e:
            logger.debug("Supabase document_chunks.select failed: %s", e)

        return []


# Global singleton repository instance
repository = DocumentRepository()
