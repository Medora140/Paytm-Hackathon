import json
import re
import uuid
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Tuple

import numpy as np

from app.errors import SarvamUnavailableError
from app.ingestion.embedder import get_embedder
from app.ml.pii import redact_pii
from app.ml.sarvam_client import sarvam_client
from app.schemas import ChatResponse, CitationItem


def _tokens(value: str) -> List[str]:
    return re.findall(r"[a-z0-9]{2,}", value.lower())


def _cosine(a: List[float], b: List[float]) -> float:
    left, right = np.array(a, dtype=np.float32), np.array(b, dtype=np.float32)
    denominator = np.linalg.norm(left) * np.linalg.norm(right)
    return float(np.dot(left, right) / denominator) if denominator else 0.0


class GroundedRAGChat:
    """Hybrid retrieval + citation-constrained Sarvam reasoning for noisy PDFs."""

    def retrieve_relevant_chunks(self, query: str, chunks: List[Dict[str, Any]], top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        if not chunks:
            return []
        embedder = get_embedder()
        query_vector = embedder.embed_query(query)
        query_terms = set(_tokens(query))
        document_frequency = Counter(term for chunk in chunks for term in set(_tokens(chunk.get("text", ""))))
        total_chunks = len(chunks)
        candidates = []
        for chunk in chunks:
            text = chunk.get("text", "")
            embedding = chunk.get("embedding")
            if isinstance(embedding, str):
                try:
                    embedding = json.loads(embedding)
                except json.JSONDecodeError:
                    embedding = None
            if not embedding:
                embedding = embedder.embed_texts([text])[0]
                chunk["embedding"] = embedding
            semantic = max(0.0, _cosine(query_vector, embedding))
            terms = set(_tokens(text)) | set(_tokens(chunk.get("clause_label", "")))
            lexical = sum(1 / (1 + document_frequency[term]) for term in query_terms & terms)
            lexical /= max(1, len(query_terms))
            # Semantic retrieval survives OCR noise; lexical overlap anchors exact clauses, fees and dates.
            candidates.append((chunk, 0.72 * semantic + 0.28 * lexical))
        candidates.sort(key=lambda item: item[1], reverse=True)

        selected: List[Tuple[Dict[str, Any], float]] = []
        selected_pages = set()
        for chunk, score in candidates:
            page = chunk.get("page_number")
            if page not in selected_pages or len(selected) < 2:
                selected.append((chunk, score))
                selected_pages.add(page)
            if len(selected) == top_k:
                break
        return selected

    def chat(self, document_id: str, question: str, chunks: List[Dict[str, Any]], language: str = "en") -> ChatResponse:
        ranked = self.retrieve_relevant_chunks(question, chunks)
        if not ranked or ranked[0][1] < 0.08:
            return self._not_found(document_id)
        relevant = [chunk for chunk, _ in ranked]
        context = "\n\n".join(
            f"[ID:{c.get('id')} | PAGE:{c.get('page_number')} | SECTION:{c.get('clause_label', 'Untitled')}]\n{redact_pii(c.get('text', ''))}"
            for c in relevant
        )
        target_language = "Hindi in Devanagari" if language.lower() in {"hi", "hindi"} else "English"
        result = sarvam_client.complete_json(f"""
Answer QUESTION in {target_language}, using only SOURCE. Explain the reasoning by connecting the relevant clause words to the answer.
Never use facts outside SOURCE. If support is insufficient set found_in_document=false.
For every citation, copy a short exact quote from the matching source section.
Return exactly {{"found_in_document":boolean,"answer":string,"citations":[{{"chunk_id":string,"page_number":number,"clause_label":string,"quote":string}}]}}.
QUESTION: {question}
SOURCE:
{context}
""")
        if not result.get("found_in_document"):
            return self._not_found(document_id)
        allowed = {str(c.get("id")): c for c in relevant}
        citations = []
        for item in result.get("citations", []):
            source = allowed.get(str(item.get("chunk_id")))
            if source:
                citations.append(CitationItem(chunk_id=str(source["id"]), page_number=int(source.get("page_number", 1)), clause_label=source.get("clause_label"), quote=str(item.get("quote", ""))[:300]))
        if not citations:
            raise SarvamUnavailableError("Sarvam response omitted source citations.")
        return ChatResponse(id=f"msg_{uuid.uuid4().hex[:12]}", document_id=document_id, role="assistant", content=str(result.get("answer", "")), cited_chunk_ids=[item.chunk_id for item in citations], citations=citations, created_at=datetime.utcnow())

    @staticmethod
    def _not_found(document_id: str) -> ChatResponse:
        return ChatResponse(id=f"msg_{uuid.uuid4().hex[:12]}", document_id=document_id, role="assistant", content="This information is not found in the provided document chunks.", cited_chunk_ids=[], citations=[], created_at=datetime.utcnow())
