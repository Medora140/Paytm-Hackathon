import json
import os
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
from app.schemas import ChatResponse, CitationItem

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

    _client_instance = None
    _connectivity_checked = False
    _is_connected = False

    def _get_client(self):
        if not self.api_key:
            print("[FALLBACK] [rag_chat] Reason: GEMINI_API_KEY is completely missing/empty in environment.")
            return None

        if GroundedRAGChat._connectivity_checked:
            return GroundedRAGChat._client_instance if GroundedRAGChat._is_connected else None

        GroundedRAGChat._connectivity_checked = True
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            # Lightweight connectivity check
            client.models.generate_content(
                model=MODEL_NAME,
                contents="ping",
                config={"max_output_tokens": 1}
            )
            GroundedRAGChat._client_instance = client
            GroundedRAGChat._is_connected = True
            print(f"[GEMINI CONNECTIVITY] Live Gemini API connection verified in RAG chat using model '{MODEL_NAME}'.")
            return client
        except Exception as e:
            GroundedRAGChat._is_connected = False
            print(f"[FALLBACK] [rag_chat] Real Gemini connectivity check failed: {type(e).__name__}: {e}")
            return None



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
                response = client.models.generate_content(
                    model=MODEL_NAME,
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
                print(f"[FALLBACK ALERT] [rag_chat] Gemini call threw exception: {type(e).__name__}: {e}")

        # 4. Fallback deterministic answering from relevant chunks
        print(f"[FALLBACK ALERT] [rag_chat] Serving deterministic extracted chunk response for doc '{document_id}' (query: '{question[:40]}...').")
        top_chunk = relevant_chunks[0]

        page_num = top_chunk["page_number"]
        label = top_chunk.get("clause_label", f"Page {page_num}")
        quote_text = top_chunk["text"][:160] + "..."

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
