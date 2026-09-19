"""Load only persisted chunks created from the user's uploaded document."""

from typing import Any, Dict, List

from app.db import get_db
from app.errors import ChunksNotFoundError


def get_chunks_for_document(document_id: str) -> List[Dict[str, Any]]:
    from app.ingestion.repository import repository

    cached = repository.get_chunks(document_id)
    if cached:
        return cached

    db = get_db()
    response = db.table("document_chunks").select("*").eq("document_id", document_id).execute()
    rows = getattr(response, "data", None) or []
    if not rows:
        raise ChunksNotFoundError(document_id, "No persisted chunks are available yet.")
    return [
        {
            "id": str(row["id"]),
            "page_number": int(row.get("page_number", 1)),
            "clause_label": row.get("clause_label") or f"Page {row.get('page_number', 1)}",
            "text": row.get("text", ""),
            "embedding": row.get("embedding"),
        }
        for row in rows
    ]
