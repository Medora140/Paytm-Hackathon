import json
import re
import uuid
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import math
from app.errors import SarvamUnavailableError
from app.ingestion.embedder import get_embedder
from app.ml.pii import redact_pii
from app.ml.sarvam_client import sarvam_client
from app.schemas import BenchmarkCompareResponse, ChatResponse, CitationItem


def _tokens(value: str) -> List[str]:
    return re.findall(r"[a-z0-9\u0900-\u097f]{2,}", value.lower())


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return float(dot / (norm_a * norm_b)) if (norm_a and norm_b) else 0.0


class GroundedRAGChat:
    """
    Hybrid retrieval + dual-context reasoning engine.
    Capable of answering detailed questions about:
    1. The uploaded user document (with exact page & clause citations)
    2. Suggested competitor policies & market benchmarks (with official website links and why they are better)
    3. Side-by-side comparative queries in English and Hindi.
    """

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

    def _format_benchmark_context(self, benchmark_data: Optional[BenchmarkCompareResponse]) -> str:
        if not benchmark_data:
            return "No additional market benchmarks available."

        lines = [f"Product Category: {benchmark_data.product_category}"]

        if benchmark_data.better_policies:
            lines.append("\n=== RECOMMENDED BETTER POLICIES ONLINE ===")
            for bp in benchmark_data.better_policies:
                adv = "; ".join(bp.key_advantages)
                lines.append(
                    f"- Policy: {bp.product_name} ({bp.issuer_name})\n"
                    f"  Official Website Link: {bp.website_url}\n"
                    f"  Why It's Better: {bp.why_better}\n"
                    f"  Key Advantages: {adv}\n"
                    f"  Estimated Potential Savings: {bp.potential_savings or 'Substantial'}"
                )

        if benchmark_data.comparables:
            lines.append("\n=== MARKET BENCHMARK POLICIES ===")
            for comp in benchmark_data.comparables:
                attrs = ", ".join([f"{k}: {v}" for k, v in comp.attributes.items()])
                lines.append(
                    f"- {comp.product_name} by {comp.issuer_name}\n"
                    f"  Official Link: {comp.source_url}\n"
                    f"  Key Attributes: {attrs}"
                )

        return "\n".join(lines)

    def chat(
        self,
        document_id: str,
        question: str,
        chunks: List[Dict[str, Any]],
        language: str = "en",
        benchmark_data: Optional[BenchmarkCompareResponse] = None
    ) -> ChatResponse:
        ranked = self.retrieve_relevant_chunks(question, chunks)
        relevant = [chunk for chunk, _ in ranked] if ranked else []

        doc_context = "\n\n".join(
            f"[ID:{c.get('id')} | PAGE:{c.get('page_number')} | SECTION:{c.get('clause_label', 'Untitled')}]\n{redact_pii(c.get('text', ''))}"
            for c in relevant
        ) if relevant else "No specific document chunks retrieved."

        benchmark_context = self._format_benchmark_context(benchmark_data)

        target_language = "Hindi in Devanagari script (शुद्ध और स्पष्ट हिंदी)" if language.lower() in {"hi", "hindi"} else "English"

        prompt = f"""
You are an expert AI financial & legal document assistant for Money Docs Decoded.
Answer the user's QUESTION in {target_language}.

You have access to two sources of information:
SOURCE 1 (USER'S UPLOADED POLICY DOCUMENT):
{doc_context}

SOURCE 2 (SUGGESTED BETTER POLICIES & MARKET BENCHMARKS ONLINE):
{benchmark_context}

Instructions:
1. If the question is about the user's policy (clauses, room rent, waiting periods, copay, exclusions, deductions), answer using SOURCE 1 and provide exact quotes and citations.
2. If the question is about suggested better policies, alternative recommendations, market comparisons, or why a competitor policy is better, answer using SOURCE 2. Always mention the policy name and include its official website link so the user can review it.
3. If the user asks a comparative question (e.g. "How does my policy compare to Care Supreme / HDFC Optima Secure?"), provide a clear, balanced side-by-side comparison between SOURCE 1 and SOURCE 2.
4. If the question cannot be answered by either SOURCE 1 or SOURCE 2, set found_in_document=false and provide a polite fallback explaining what was checked.
5. For citations from the user's document, include chunk_id, page_number, clause_label, and quote.
6. For suggested policies referenced in your answer, list their policy names under `suggested_policies_referenced`.

Return strictly valid JSON with this exact schema:
{{
  "found_in_document": boolean,
  "answer": string,
  "citations": [{{"chunk_id": string, "page_number": number, "clause_label": string, "quote": string}}],
  "suggested_policies_referenced": [string]
}}

QUESTION: {question}
"""

        try:
            result = sarvam_client.complete_json(prompt)
        except Exception as exc:
            raise SarvamUnavailableError(f"Chat generation failed: {exc}")

        if not result.get("found_in_document") and not result.get("answer"):
            return self._not_found(document_id, language)

        answer_text = str(result.get("answer", ""))
        if not answer_text.strip():
            return self._not_found(document_id, language)

        allowed = {str(c.get("id")): c for c in relevant}
        citations = []
        for item in result.get("citations", []):
            cid = str(item.get("chunk_id", ""))
            source = allowed.get(cid)
            if source:
                citations.append(CitationItem(
                    chunk_id=str(source.get("id", cid)),
                    page_number=int(source.get("page_number", item.get("page_number", 1))),
                    clause_label=source.get("clause_label") or item.get("clause_label"),
                    quote=str(item.get("quote", ""))[:300]
                ))
            elif item.get("quote"):
                # Chunk citation generated by LLM
                citations.append(CitationItem(
                    chunk_id=cid or f"chunk_{uuid.uuid4().hex[:8]}",
                    page_number=int(item.get("page_number", 1)),
                    clause_label=item.get("clause_label"),
                    quote=str(item.get("quote", ""))[:300]
                ))

        policies_ref = [str(p) for p in result.get("suggested_policies_referenced", []) if p]

        return ChatResponse(
            id=f"msg_{uuid.uuid4().hex[:12]}",
            document_id=document_id,
            role="assistant",
            content=answer_text,
            cited_chunk_ids=[item.chunk_id for item in citations],
            citations=citations,
            suggested_policies_referenced=policies_ref,
            created_at=datetime.utcnow()
        )

    @staticmethod
    def _not_found(document_id: str, language: str = "en") -> ChatResponse:
        content = (
            "यह जानकारी आपके द्वारा दिए गए दस्तावेज़ या अनुशंसित पॉलिसियों में नहीं मिली है। कृपया किसी अन्य खंड या पॉलिसी के बारे में पूछें।"
            if language.lower() in {"hi", "hindi"}
            else "This information was not found in the provided document or market benchmarks. Please try asking about specific clauses, room rent limits, waiting periods, or suggested alternative policies."
        )
        return ChatResponse(
            id=f"msg_{uuid.uuid4().hex[:12]}",
            document_id=document_id,
            role="assistant",
            content=content,
            cited_chunk_ids=[],
            citations=[],
            suggested_policies_referenced=[],
            created_at=datetime.utcnow()
        )
