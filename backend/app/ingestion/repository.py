import uuid
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional
from app.db import StubSupabaseClient, get_db
from app.runtime_flags import allow_in_memory_stores
from app.schemas import DocumentStatus, DocumentType

logger = logging.getLogger(__name__)


def _parse_iso_timestamp(val: Any) -> datetime:
    if not val:
        return datetime.utcnow()
    if isinstance(val, datetime):
        return val
    try:
        from dateutil.parser import isoparse
        return isoparse(str(val))
    except Exception:
        try:
            return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
        except Exception:
            return datetime.utcnow()


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

        persist_error = self._persist_document_insert(doc_data)
        if persist_error and not allow_in_memory_stores():
            raise RuntimeError(f"Failed to persist document '{doc_id}' to Supabase: {persist_error}")
        if persist_error:
            logger.error("Supabase documents.insert failed (in-memory allowed): %s", persist_error)

        return doc_data

    def _persist_document_insert(self, doc_data: Dict[str, Any]) -> Optional[str]:
        try:
            db = get_db()
            if isinstance(db, StubSupabaseClient) or db.__class__.__name__ == "StubSupabaseClient":
                return "StubSupabaseClient cannot persist documents"
            payload = {
                "id": doc_data["id"],
                "user_id": doc_data["user_id"],
                "filename": doc_data["filename"],
                "document_type": doc_data["document_type"],
                "storage_path": doc_data["storage_path"],
                "status": DocumentStatus.UPLOADED.value,
                "issuer_name": doc_data.get("issuer_name"),
                "uploaded_at": doc_data["uploaded_at"].isoformat()
                if hasattr(doc_data["uploaded_at"], "isoformat")
                else str(doc_data["uploaded_at"]),
            }
            # Use upsert with on_conflict="id" to avoid duplicate key crash on background runs
            db.table("documents").upsert(payload, on_conflict="id").execute()
            return None
        except Exception as e:
            logger.exception("Supabase documents.upsert failed: %s", e)
            return f"{type(e).__name__}: {e}"

    def update_status(
        self,
        doc_id: str,
        status: DocumentStatus,
        pipeline_stage: str,
        issuer_name: Optional[str] = None,
        document_type: Optional[DocumentType] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Updates document status, pipeline stage description, and optional detected issuer/type.
        """
        doc = self._documents.get(doc_id)
        if doc:
            doc["status"] = status
            doc["pipeline_stage"] = pipeline_stage
            if issuer_name:
                doc["issuer_name"] = issuer_name
            if document_type:
                doc["document_type"] = document_type.value if hasattr(document_type, "value") else str(document_type)

        # Attempt writing to Supabase
        try:
            db = get_db()
            if not isinstance(db, StubSupabaseClient) and db.__class__.__name__ != "StubSupabaseClient":
                payload: Dict[str, Any] = {"status": status.value if hasattr(status, "value") else str(status)}
                if issuer_name:
                    payload["issuer_name"] = issuer_name
                if document_type:
                    payload["document_type"] = document_type.value if hasattr(document_type, "value") else str(document_type)
                db.table("documents").update(payload).eq("id", doc_id).execute()
        except Exception as e:
            logger.error("Supabase documents.update failed: %s", e)
            if not allow_in_memory_stores():
                raise

        return doc

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves document metadata by ID directly from Supabase.
        Maintains live in-memory stage information for ongoing tasks.
        """
        try:
            db = get_db()
            if not isinstance(db, StubSupabaseClient) and db.__class__.__name__ != "StubSupabaseClient":
                res = db.table("documents").select("*").eq("id", doc_id).execute()
                if hasattr(res, "data") and res.data:
                    item = res.data[0]
                    # Preserve live pipeline stage from memory cache if active
                    cached = self._documents.get(doc_id, {})
                    live_stage = cached.get("pipeline_stage") or f"Status: {item.get('status')}"
                    doc = {
                        "id": item.get("id"),
                        "user_id": item.get("user_id"),
                        "filename": item.get("filename"),
                        "document_type": DocumentType(item.get("document_type", "health_insurance")),
                        "storage_path": item.get("storage_path"),
                        "status": DocumentStatus(item.get("status", "uploaded")),
                        "pipeline_stage": live_stage,
                        "issuer_name": item.get("issuer_name"),
                        "uploaded_at": _parse_iso_timestamp(item.get("uploaded_at")),
                        "deleted_at": None,
                        "confidence_score": None
                    }
                    self._documents[doc_id] = doc
                    return doc
        except Exception as e:
            logger.error("Supabase documents.select failed: %s", e)
            if not allow_in_memory_stores():
                raise

        if doc_id in self._documents:
            return self._documents[doc_id]

        return None

    def list_documents(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lists documents directly from Supabase. If guest user or no user_id, returns all documents.
        """
        try:
            db = get_db()
            if not isinstance(db, StubSupabaseClient) and db.__class__.__name__ != "StubSupabaseClient":
                q = db.table("documents").select("*").order("uploaded_at", desc=True)
                # Filter by user_id only if authenticated and not the default guest ID
                if user_id and user_id != "00000000-0000-0000-0000-000000000000":
                    q = q.eq("user_id", user_id)
                res = q.execute()
                docs = []
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
                            "uploaded_at": _parse_iso_timestamp(item.get("uploaded_at")),
                            "confidence_score": None
                        }
                        self._documents[d_id] = doc
                        docs.append(doc)
                return docs
        except Exception as e:
            logger.error("Supabase documents.select all failed: %s", e)
            if not allow_in_memory_stores():
                raise

        if allow_in_memory_stores():
            docs = list(self._documents.values())
            if user_id and user_id != "00000000-0000-0000-0000-000000000000":
                docs = [d for d in docs if d.get("user_id") == user_id]
            return docs

        return []

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
            logger.error("Supabase documents.delete error: %s", e)
            if not allow_in_memory_stores():
                raise

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

        persist_error = self._persist_chunks(doc_id, chunk_records, now)
        if persist_error and not allow_in_memory_stores():
            raise RuntimeError(
                f"Failed to persist document_chunks for '{doc_id}' to Supabase: {persist_error}"
            )
        if persist_error:
            logger.error("Supabase document_chunks.insert failed (in-memory allowed): %s", persist_error)

        return len(chunk_records)

    def _format_embedding(self, embedding: Any) -> Optional[str]:
        if not embedding:
            return None
        if isinstance(embedding, str):
            return embedding
        try:
            values = [float(x) for x in embedding]
            return "[" + ",".join(f"{v:.8f}" for v in values) + "]"
        except Exception:
            return None

    def _persist_chunks(self, doc_id: str, chunk_records: List[Dict[str, Any]], now: datetime) -> Optional[str]:
        try:
            db = get_db()
            if db.__class__.__name__ == "StubSupabaseClient":
                return "StubSupabaseClient cannot persist document_chunks"
            supabase_rows = []
            for r in chunk_records:
                chunk_id = r["id"]
                try:
                    uuid.UUID(str(chunk_id))
                except Exception:
                    chunk_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}:{r['id']}"))
                    r["id"] = chunk_id
                supabase_rows.append({
                    "id": chunk_id,
                    "document_id": r["document_id"],
                    "page_number": r["page_number"],
                    "clause_label": r["clause_label"],
                    "text": r["text"],
                    "embedding": self._format_embedding(r.get("embedding")),
                    "created_at": now.isoformat()
                })
            for i in range(0, len(supabase_rows), 50):
                batch = supabase_rows[i : i + 50]
                db.table("document_chunks").insert(batch).execute()
            logger.info("Persisted %s document_chunks to Supabase for '%s'", len(supabase_rows), doc_id)
            return None
        except Exception as e:
            logger.exception("Supabase document_chunks.insert failed: %s", e)
            return f"{type(e).__name__}: {e}"

    def get_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        Returns all chunks for a given document directly from Supabase.
        Falls back to local memory if Supabase is temporarily unreachable.
        """
        try:
            db = get_db()
            if not isinstance(db, StubSupabaseClient) and db.__class__.__name__ != "StubSupabaseClient":
                res = db.table("document_chunks").select("*").eq("document_id", doc_id).order("page_number").execute()
                if hasattr(res, "data") and res.data is not None and len(res.data) > 0:
                    data = res.data
                    for row in data:
                        raw_emb = row.get("embedding")
                        if isinstance(raw_emb, str):
                            try:
                                import json
                                row["embedding"] = json.loads(raw_emb)
                            except Exception:
                                row["embedding"] = [float(x) for x in raw_emb.strip("[]").split(",") if x.strip()]
                    self._chunks[doc_id] = data
                    return data
        except Exception as e:
            logger.error("Supabase document_chunks.select failed: %s", e)
            if not allow_in_memory_stores():
                raise

        if doc_id in self._chunks and len(self._chunks[doc_id]) > 0:
            return self._chunks[doc_id]

        return []


# Global singleton repository instance
repository = DocumentRepository()
