import json
import logging
import os
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
from app.schemas import ChatResponse, CitationItem
from app.ml.gemini_client import (
    get_gemini_client,
    get_last_gemini_error,
    probe_gemini_connectivity,
    generate_gemini_content,
)

logger = logging.getLogger("app.ml.rag_chat")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Out-of-scope keywords that trigger immediate refusal
OUT_OF_SCOPE_TOPICS = [
    "capital of", "weather in", "how to cook", "recipe", "who is the president",
    "stock price of apple", "prescribe", "antibiotics", "medical diagnosis",
    "pasta carbonara", "write a poem", "who won the", "football score"
]


def _lexical_similarity(query: str, text: str) -> float:
    """
    Computes a normalized keyword overlap score between query and chunk text.
    """
    stop_words = {"the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "or", "is", "are", "what", "how", "why", "when", "does", "do", "i", "my"}
    query_tokens = set(re.findall(r"\b\w{3,}\b", query.lower())) - stop_words
    if not query_tokens:
        return 0.0
    text_lower = text.lower()
    matches = sum(1 for token in query_tokens if token in text_lower)
    return matches / len(query_tokens)


class GroundedRAGChat:
    """
    Grounded RAG Conversational Engine adhering strictly to §4 guardrails:
    - Answers only from retrieved chunks
    - Rejects questions unsupported by the provided document chunks
    - Cites page numbers and exact quotes
    """

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.api_key = gemini_api_key or GEMINI_API_KEY

    def _get_client(self):
        """Returns the cached verified Gemini client instance, or None if unavailable."""
        return get_gemini_client(api_key=self.api_key)



    def retrieve_relevant_chunks(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int = 3
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Retrieves the top-k most relevant chunks using lexical similarity.
        """
        scored_chunks = []
        for chunk in chunks:
            text = chunk.get("text", "")
            score = _lexical_similarity(query, text)
            # Boost if query matches clause label
            label = chunk.get("clause_label", "")
            if label and _lexical_similarity(query, label) > 0.3:
                score += 0.3
            scored_chunks.append((chunk, score))

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:top_k]

    def chat(
        self,
        document_id: str,
        question: str,
        chunks: List[Dict[str, Any]],
        language: str = "en"
    ) -> ChatResponse:
        """
        Executes grounded Q&A over the document chunks.
        If the question is out of scope or not found in chunks, returns refusal.
        """
        q_lower = question.lower()
        
        # 1. Quick Guardrail Check: Disallowed / Out-of-Scope query
        if any(topic in q_lower for topic in OUT_OF_SCOPE_TOPICS):
            return ChatResponse(
                id=f"msg_{uuid.uuid4().hex[:12]}",
                document_id=document_id,
                role="assistant",
                content=(
                    "This information is not found in the provided document chunks. "
                    "I am strictly configured to answer questions grounded in your uploaded document."
                ),
                cited_chunk_ids=[],
                citations=[],
                created_at=datetime.utcnow()
            )

        # 2. Retrieve top chunks
        top_scored = self.retrieve_relevant_chunks(question, chunks, top_k=3)
        relevant_chunks = [item[0] for item in top_scored if item[1] > 0.05]

        # If zero chunks match the user question, refuse
        if not relevant_chunks or (top_scored and top_scored[0][1] == 0.0):
            return ChatResponse(
                id=f"msg_{uuid.uuid4().hex[:12]}",
                document_id=document_id,
                role="assistant",
                content=(
                    "This information is not found in the provided document chunks. "
                    "The document does not contain details related to your query."
                ),
                cited_chunk_ids=[],
                citations=[],
                created_at=datetime.utcnow()
            )

        # 3. Formulate Prompt & Call Gemini
        client = self._get_client()
        last_error = get_last_gemini_error() or "Gemini client unavailable or offline"

        if client is not None:
            try:
                from google.genai import types

                chunks_context = "\n\n".join([
                    f"[Chunk ID: {c.get('id')} | Page: {c.get('page_number')} | Section: {c.get('clause_label', '')}]\n{c.get('text', '')}"
                    for c in relevant_chunks
                ])

                prompt = f"""
You are a trusted financial document assistant for Money Docs Decoded.
Answer the user's question using ONLY the provided document chunks below.

STRICT GUARDRAILS:
1. You must answer ONLY from the provided chunks. DO NOT extrapolate, assume, or bring in outside world knowledge.
2. If the answer is NOT explicitly supported by the provided chunks, reply with:
   "This information is not found in the provided document chunks."
3. If the answer is supported, provide a clear, plain-language answer and list the cited chunks.

DOCUMENT CHUNKS:
{chunks_context}

USER QUESTION:
{question}
"""
                logger.info(
                    "[LIVE GEMINI CALL] [rag_chat] Initiating live Gemini RAG chat (model=%s, doc_id=%s, question='%s')...",
                    MODEL_NAME,
                    document_id,
                    question[:50]
                )

                response, used_model = generate_gemini_content(
                    client=client,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema={
                            "type": "OBJECT",
                            "properties": {
                                "found_in_document": {"type": "BOOLEAN"},
                                "answer": {"type": "STRING"},
                                "cited_chunk_ids": {
                                    "type": "ARRAY",
                                    "items": {"type": "STRING"}
                                },
                                "citations": {
                                    "type": "ARRAY",
                                    "items": {
                                        "type": "OBJECT",
                                        "properties": {
                                            "chunk_id": {"type": "STRING"},
                                            "page_number": {"type": "INTEGER"},
                                            "clause_label": {"type": "STRING"},
                                            "quote": {"type": "STRING"}
                                        },
                                        "required": ["chunk_id", "page_number", "quote"]
                                    }
                                }
                            },
                            "required": ["found_in_document", "answer"]
                        },
                        temperature=0.1
                    )
                )

                result_data = json.loads(response.text)
                if not result_data.get("found_in_document", True) or "not found" in result_data.get("answer", "").lower():
                    logger.info("[RAG GUARDRAIL] [rag_chat] Live response indicates question is unsupported by chunks for doc '%s'.", document_id)
                    return ChatResponse(
                        id=f"msg_{uuid.uuid4().hex[:12]}",
                        document_id=document_id,
                        role="assistant",
                        content="This information is not found in the provided document chunks.",
                        cited_chunk_ids=[],
                        citations=[],
                        created_at=datetime.utcnow()
                    )

                # Assemble citations
                citations = []
                for c_item in result_data.get("citations", []):
                    citations.append(
                        CitationItem(
                            chunk_id=c_item.get("chunk_id", relevant_chunks[0]["id"]),
                            page_number=c_item.get("page_number", relevant_chunks[0]["page_number"]),
                            clause_label=c_item.get("clause_label", relevant_chunks[0].get("clause_label")),
                            quote=c_item.get("quote", relevant_chunks[0]["text"][:100])
                        )
                    )

                cited_ids = result_data.get("cited_chunk_ids") or [c.chunk_id for c in citations]
                if not cited_ids and citations:
                    cited_ids = [c.chunk_id for c in citations]

                logger.info(
                    "[LIVE GEMINI SUCCESS] [rag_chat] Successfully generated live RAG response for doc '%s' (model=%s, cited_chunks=%d)",
                    document_id,
                    MODEL_NAME,
                    len(cited_ids)
                )

                return ChatResponse(
                    id=f"msg_{uuid.uuid4().hex[:12]}",
                    document_id=document_id,
                    role="assistant",
                    content=result_data["answer"],
                    cited_chunk_ids=cited_ids,
                    citations=citations,
                    created_at=datetime.utcnow()
                )

            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                logger.warning(
                    "\n" + "=" * 68 + "\n"
                    "[FALLBACK WARNING] [rag_chat] Live Gemini RAG call FAILED for doc '%s'!\n"
                    "Reason: %s: %s\n"
                    "Model: %s\n"
                    "Action: Falling back to deterministic extracted chunk response.\n"
                    + "=" * 68,
                    document_id,
                    type(e).__name__,
                    e,
                    MODEL_NAME
                )

        # 4. Fallback deterministic answering from relevant chunks
        top_chunk = relevant_chunks[0]
        page_num = top_chunk["page_number"]
        label = top_chunk.get("clause_label", f"Page {page_num}")
        quote_text = top_chunk["text"][:160] + "..."

        logger.warning(
            "\n" + "=" * 68 + "\n"
            "[FALLBACK WARNING] [rag_chat] Serving fallback deterministic extracted chunk response for doc '%s'!\n"
            "Reason: %s\n"
            "Query: '%s'\n"
            "Action: Extracting grounded quote from top chunk ID '%s' (Page %s).\n"
            + "=" * 68,
            document_id,
            last_error,
            question[:80],
            top_chunk["id"],
            page_num
        )

        return ChatResponse(
            id=f"msg_{uuid.uuid4().hex[:12]}",
            document_id=document_id,
            role="assistant",
            content=f"According to {label} (Page {page_num}): {top_chunk['text']}",
            cited_chunk_ids=[top_chunk["id"]],
            citations=[
                CitationItem(
                    chunk_id=top_chunk["id"],
                    page_number=page_num,
                    clause_label=label,
                    quote=quote_text
                )
            ],
            created_at=datetime.utcnow()
        )
