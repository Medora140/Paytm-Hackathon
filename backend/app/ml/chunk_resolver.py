"""Load only persisted chunks created from the user's uploaded document."""

import json
import logging
from typing import Any, Dict, List

from app.errors import ChunksNotFoundError

logger = logging.getLogger(__name__)


def get_chunks_for_document(document_id: str) -> List[Dict[str, Any]]:
    """
    Returns all embedded chunks for a document.
    First checks the ingestion repository (Supabase + in-memory fallback).
    Raises ChunksNotFoundError only if no chunks are available at all.
    """
    from app.ingestion.repository import repository

    # repository.get_chunks() already handles Supabase query + in-memory fallback
    chunks = repository.get_chunks(document_id)
    if chunks:
        return chunks

    raise ChunksNotFoundError(document_id, "No persisted chunks are available yet.")
