import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.db import StubSupabaseClient, get_db
from app.runtime_flags import allow_in_memory_stores
from app.schemas import (
    ConfidenceScoreResponse,
    DocumentSummaryResponse,
    RedFlagItem,
    ScoreBreakdownItem,
    SeverityLevel,
)

logger = logging.getLogger("app.ml.repository")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


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


class MLRepository:
    """
    Repository layer for ML analysis persistence matching 05-database-schema.md.
    Supabase-first implementation with in-memory caching fallback for test suites.
    Manages:
      - document_summaries
      - red_flags
      - confidence_scores
      - chat_messages
    """

    def __init__(self):
        # In-memory stores for testing and cache reflection
        self._summaries: Dict[str, Dict[str, Any]] = {}  # key: f"{doc_id}_{lang}"
        self._red_flags: Dict[str, List[Dict[str, Any]]] = {}  # key: doc_id
        self._confidence_scores: Dict[str, Dict[str, Any]] = {}  # key: doc_id
        self._chat_messages: Dict[str, List[Dict[str, Any]]] = {}  # key: doc_id

    # -------------------------------------------------------------------------
    # 1. Document Summaries
    # -------------------------------------------------------------------------

    def get_summary(
        self,
        document_id: str,
        language: str = "en"
    ) -> Optional[DocumentSummaryResponse]:
        """
        Retrieves cached document summary for document_id and language from Supabase.
        """
        cache_key = f"{document_id}_{language.lower()}"
        try:
            db = get_db()
            if not isinstance(db, StubSupabaseClient) and db.__class__.__name__ != "StubSupabaseClient":
                res = (
                    db.table("document_summaries")
                    .select("*")
                    .eq("document_id", document_id)
                    .eq("language", language.lower())
                    .execute()
                )
                if hasattr(res, "data") and res.data:
                    row = res.data[0]
                    summary = DocumentSummaryResponse(
                        id=str(row.get("id", f"sum_{uuid.uuid4().hex[:12]}")),
                        document_id=row.get("document_id", document_id),
                        language=row.get("language", language),
                        coverage=row.get("coverage", []) or [],
                        exclusions=row.get("exclusions", []) or [],
                        key_fees=row.get("key_fees", []) or [],
                        waiting_periods=row.get("waiting_periods", []) or [],
                        notable_terms=row.get("notable_terms", []) or [],
                        model_version=row.get("model_version", "persisted"),
                        is_fallback=False,
                        generated_at=_parse_iso_timestamp(row.get("generated_at"))
                    )
                    self._summaries[cache_key] = summary.model_dump()
                    logger.info("Retrieved cached summary from Supabase for doc '%s' (lang=%s)", document_id, language)
                    return summary
        except Exception as e:
            logger.warning("Supabase document_summaries.select failed: %s", e)
            if not allow_in_memory_stores():
                raise

        if allow_in_memory_stores() and cache_key in self._summaries:
            data = self._summaries[cache_key]
            return DocumentSummaryResponse(**data)

        return None

    def save_summary(
        self,
        summary: DocumentSummaryResponse
    ) -> DocumentSummaryResponse:
        """
        Persists document summary to Supabase document_summaries table.
        """
        cache_key = f"{summary.document_id}_{summary.language.lower()}"
        self._summaries[cache_key] = summary.model_dump()

        now_str = summary.generated_at.isoformat() if hasattr(summary.generated_at, "isoformat") else str(summary.generated_at)
        record = {
            "document_id": summary.document_id,
            "language": summary.language.lower(),
            "coverage": summary.coverage,
            "exclusions": summary.exclusions,
            "key_fees": summary.key_fees,
            "waiting_periods": summary.waiting_periods,
            "notable_terms": summary.notable_terms,
            "model_version": summary.model_version,
            "generated_at": now_str,
        }

        try:
            db = get_db()
            if not isinstance(db, StubSupabaseClient) and db.__class__.__name__ != "StubSupabaseClient":
                # Upsert on document_id + language unique constraint
                res = db.table("document_summaries").upsert(
                    record,
                    on_conflict="document_id,language"
                ).execute()
                if hasattr(res, "data") and res.data:
                    record["id"] = str(res.data[0].get("id"))
                logger.info("Persisted document_summaries to Supabase for doc '%s' (lang=%s)", summary.document_id, summary.language)
        except Exception as e:
            logger.error("Supabase document_summaries.upsert failed: %s", e)
            if not allow_in_memory_stores():
                raise

        return summary

    # -------------------------------------------------------------------------
    # 2. Red Flags
    # -------------------------------------------------------------------------

    def get_red_flags(
        self,
        document_id: str
    ) -> Optional[List[RedFlagItem]]:
        """
        Retrieves persisted red flags for document_id from Supabase.
        """
        try:
            db = get_db()
            if not isinstance(db, StubSupabaseClient) and db.__class__.__name__ != "StubSupabaseClient":
                res = db.table("red_flags").select("*").eq("document_id", document_id).execute()
                if hasattr(res, "data") and res.data:
                    items = []
                    for row in res.data:
                        severity_val = row.get("severity", "medium")
                        try:
                            sev = SeverityLevel(severity_val)
                        except Exception:
                            sev = SeverityLevel.MEDIUM
                        items.append(
                            RedFlagItem(
                                id=str(row.get("id")),
                                document_id=str(row.get("document_id")),
                                pattern_id=str(row.get("pattern_id")) if row.get("pattern_id") else None,
                                chunk_id=str(row.get("chunk_id")) if row.get("chunk_id") else None,
                                page_number=int(row.get("page_number") or 1),
                                clause_label=row.get("clause_label") or None,
                                source_text=row.get("plain_explanation") or "",
                                severity=sev,
                                plain_explanation=row.get("plain_explanation") or "",
                                confirmed_by_llm=bool(row.get("confirmed_by_llm", True)),
                                created_at=_parse_iso_timestamp(row.get("created_at"))
                            )
                        )
                    self._red_flags[document_id] = [it.model_dump() for it in items]
                    logger.info("Retrieved %d cached red_flags from Supabase for doc '%s'", len(items), document_id)
                    return items
        except Exception as e:
            logger.warning("Supabase red_flags.select failed: %s", e)
            if not allow_in_memory_stores():
                raise

        if allow_in_memory_stores() and document_id in self._red_flags:
            return [RedFlagItem(**item) for item in self._red_flags[document_id]]

        return None

    def save_red_flags(
        self,
        document_id: str,
        flags: List[RedFlagItem]
    ) -> List[RedFlagItem]:
        """
        Persists detected red flags into the red_flags Supabase table.
        """
        self._red_flags[document_id] = [f.model_dump() for f in flags]

        if not flags:
            return flags

        supabase_rows = []
        for f in flags:
            row: Dict[str, Any] = {
                "document_id": document_id,
                "severity": f.severity.value if hasattr(f.severity, "value") else str(f.severity),
                "plain_explanation": f.plain_explanation,
                "confirmed_by_llm": f.confirmed_by_llm,
                "created_at": f.created_at.isoformat() if hasattr(f.created_at, "isoformat") else str(f.created_at),
            }
            # Only set pattern_id and chunk_id if valid UUIDs to respect foreign keys
            if f.pattern_id:
                try:
                    uuid.UUID(str(f.pattern_id))
                    row["pattern_id"] = str(f.pattern_id)
                except Exception:
                    pass  # Non-UUID pattern_id (e.g. string tag) left null for FK safety
            if f.chunk_id:
                try:
                    uuid.UUID(str(f.chunk_id))
                    row["chunk_id"] = str(f.chunk_id)
                except Exception:
                    pass

            supabase_rows.append(row)

        try:
            db = get_db()
            if not isinstance(db, StubSupabaseClient) and db.__class__.__name__ != "StubSupabaseClient":
                # Delete existing flags for document before inserting fresh batch
                db.table("red_flags").delete().eq("document_id", document_id).execute()
                if supabase_rows:
                    db.table("red_flags").insert(supabase_rows).execute()
                logger.info("Persisted %d red_flags to Supabase for doc '%s'", len(supabase_rows), document_id)
        except Exception as e:
            logger.error("Supabase red_flags.insert failed: %s", e)
            if not allow_in_memory_stores():
                raise

        return flags

    # -------------------------------------------------------------------------
    # 3. Confidence Scores
    # -------------------------------------------------------------------------

    def get_confidence_score(
        self,
        document_id: str
    ) -> Optional[ConfidenceScoreResponse]:
        """
        Retrieves cached confidence score from Supabase confidence_scores table.
        """
        try:
            db = get_db()
            if not isinstance(db, StubSupabaseClient) and db.__class__.__name__ != "StubSupabaseClient":
                res = (
                    db.table("confidence_scores")
                    .select("*")
                    .eq("document_id", document_id)
                    .order("computed_at", desc=True)
                    .limit(1)
                    .execute()
                )
                if hasattr(res, "data") and res.data:
                    row = res.data[0]
                    breakdown_items = []
                    for b in row.get("breakdown", []):
                        if isinstance(b, dict):
                            breakdown_items.append(ScoreBreakdownItem(reason=b.get("reason", ""), points=int(b.get("points", 0))))
                    score_res = ConfidenceScoreResponse(
                        id=str(row.get("id")),
                        document_id=str(row.get("document_id")),
                        score=int(row.get("score", 0)),
                        breakdown=breakdown_items,
                        kb_version=str(row.get("kb_version", "")),
                        computed_at=_parse_iso_timestamp(row.get("computed_at"))
                    )
                    self._confidence_scores[document_id] = score_res.model_dump()
                    logger.info("Retrieved cached confidence_score (%d/100) from Supabase for doc '%s'", score_res.score, document_id)
                    return score_res
        except Exception as e:
            logger.warning("Supabase confidence_scores.select failed: %s", e)
            if not allow_in_memory_stores():
                raise

        if allow_in_memory_stores() and document_id in self._confidence_scores:
            return ConfidenceScoreResponse(**self._confidence_scores[document_id])

        return None

    def save_confidence_score(
        self,
        score: ConfidenceScoreResponse
    ) -> ConfidenceScoreResponse:
        """
        Persists confidence score to Supabase confidence_scores table.
        """
        self._confidence_scores[score.document_id] = score.model_dump()

        record = {
            "document_id": score.document_id,
            "score": score.score,
            "breakdown": [item.model_dump() for item in score.breakdown],
            "kb_version": score.kb_version,
            "computed_at": score.computed_at.isoformat() if hasattr(score.computed_at, "isoformat") else str(score.computed_at),
        }

        try:
            db = get_db()
            if not isinstance(db, StubSupabaseClient) and db.__class__.__name__ != "StubSupabaseClient":
                # Delete older score and insert current
                db.table("confidence_scores").delete().eq("document_id", score.document_id).execute()
                db.table("confidence_scores").insert(record).execute()
                logger.info("Persisted confidence_score (%d/100) to Supabase for doc '%s'", score.score, score.document_id)
        except Exception as e:
            logger.error("Supabase confidence_scores.insert failed: %s", e)
            if not allow_in_memory_stores():
                raise

        return score

    # -------------------------------------------------------------------------
    # 4. Chat Messages
    # -------------------------------------------------------------------------

    def save_chat_message(
        self,
        document_id: str,
        user_id: str,
        role: str,
        content: str,
        cited_chunk_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Persists a chat message (user or assistant) into the chat_messages table.
        """
        msg_id = str(uuid.uuid4())
        now = datetime.utcnow()
        clean_chunk_ids = []
        for c in (cited_chunk_ids or []):
            try:
                clean_chunk_ids.append(str(c))
            except Exception:
                pass

        record = {
            "id": msg_id,
            "document_id": document_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "cited_chunk_ids": clean_chunk_ids,
            "created_at": now.isoformat()
        }

        if document_id not in self._chat_messages:
            self._chat_messages[document_id] = []
        self._chat_messages[document_id].append(record)

        try:
            db = get_db()
            if not isinstance(db, StubSupabaseClient) and db.__class__.__name__ != "StubSupabaseClient":
                db.table("chat_messages").insert(record).execute()
                logger.info("Persisted chat_message (%s) to Supabase for doc '%s'", role, document_id)
        except Exception as e:
            logger.error("Supabase chat_messages.insert failed: %s", e)
            if not allow_in_memory_stores():
                raise

        return record

    def get_chat_history(
        self,
        document_id: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieves chat history for a document from Supabase.
        """
        try:
            db = get_db()
            if not isinstance(db, StubSupabaseClient) and db.__class__.__name__ != "StubSupabaseClient":
                res = (
                    db.table("chat_messages")
                    .select("*")
                    .eq("document_id", document_id)
                    .order("created_at")
                    .execute()
                )
                if hasattr(res, "data") and res.data:
                    self._chat_messages[document_id] = res.data
                    return res.data
        except Exception as e:
            logger.warning("Supabase chat_messages.select failed: %s", e)
            if not allow_in_memory_stores():
                raise

        return self._chat_messages.get(document_id, [])


# Global singleton instance
ml_repository = MLRepository()
