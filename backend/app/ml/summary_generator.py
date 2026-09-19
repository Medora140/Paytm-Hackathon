import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.errors import SarvamUnavailableError
from app.ml.pii import redact_pii
from app.ml.sarvam_client import sarvam_client
from app.schemas import DocumentSummaryResponse


def _summarise_chunk_texts(chunks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    coverage: List[str] = []
    exclusions: List[str] = []
    key_fees: List[str] = []
    waiting_periods: List[str] = []
    notable_terms: List[str] = []

    for chunk in chunks:
        text = (chunk.get("text") or "").strip()
        label = chunk.get("clause_label") or f"Page {chunk.get('page_number', 1)}"
        page_ref = f" (Page {chunk.get('page_number', 1)})"
        if not text:
            continue
        lower = text.lower()

        if any(token in lower for token in ["coverage", "sum insured", "hospitalisation", "benefit", "insured amount", "reimbursement", "cashless"]):
            coverage.append(f"{label}: {text[:220]}{page_ref}")

        if any(token in lower for token in ["exclusion", "not covered", "not payable", "waiting period", "pre-existing", "deductible", "copay", "co-pay"]):
            exclusions.append(f"{label}: {text[:220]}{page_ref}")

        if any(token in lower for token in ["room rent", "co-pay", "premium", "fee", "deduction", "sub limit", "loading", "expense ratio"]):
            key_fees.append(f"{label}: {text[:220]}{page_ref}")

        if any(token in lower for token in ["waiting period", "pre-existing", "cooling off", "lock-in", "lock in", "exit load"]):
            waiting_periods.append(f"{label}: {text[:220]}{page_ref}")

        if len(text) > 80 and not any(token in lower for token in ["policy", "document", "uploaded"]):
            notable_terms.append(f"{label}: {text[:220]}{page_ref}")

    fallback = {
        "coverage": coverage or [f"Document coverage details are present in the uploaded clauses.{(' (Page 1)' if chunks else '')}"],
        "exclusions": exclusions or [f"No explicit exclusion language was isolated from the uploaded text.{(' (Page 1)' if chunks else '')}"],
        "key_fees": key_fees or [f"Key financial terms should be reviewed directly in the uploaded document.{(' (Page 1)' if chunks else '')}"],
        "waiting_periods": waiting_periods or [f"Waiting periods were not clearly identifiable from the available text.{(' (Page 1)' if chunks else '')}"],
        "notable_terms": notable_terms or [f"The uploaded policy contains text that requires manual review for clause-specific interpretation.{(' (Page 1)' if chunks else '')}"],
    }
    return fallback


def generate_fallback_summary(document_id: str, chunks: List[Dict[str, Any]], language: str = "en") -> DocumentSummaryResponse:
    """Create a deterministic summary when remote AI services are not configured."""
    if not chunks:
        # Document is still being processed — return a placeholder summary
        placeholder_msg = (
            "दस्तावेज़ अभी प्रोसेस हो रहा है। कृपया कुछ देर बाद पुनः लोड करें।"
            if language.lower() in {"hi", "hindi"}
            else "Document is still being processed. Please reload in a moment."
        )
        return DocumentSummaryResponse(
            id=f"sum_{uuid.uuid4().hex[:12]}",
            document_id=document_id,
            language=language.lower() if language else "en",
            coverage=[placeholder_msg],
            exclusions=[],
            key_fees=[],
            waiting_periods=[],
            notable_terms=[],
            model_version="local-fallback-summary",
            generated_at=datetime.utcnow(),
        )

    fallback = _summarise_chunk_texts(chunks)
    language_tag = language.lower() if language else "en"
    return DocumentSummaryResponse(
        id=f"sum_{uuid.uuid4().hex[:12]}",
        document_id=document_id,
        language=language_tag,
        coverage=[str(v) for v in fallback["coverage"][:3]],
        exclusions=[str(v) for v in fallback["exclusions"][:3]],
        key_fees=[str(v) for v in fallback["key_fees"][:3]],
        waiting_periods=[str(v) for v in fallback["waiting_periods"][:3]],
        notable_terms=[str(v) for v in fallback["notable_terms"][:3]],
        model_version="local-fallback-summary",
        generated_at=datetime.utcnow(),
    )


def generate_plain_language_summary(document_id: str, chunks: List[Dict[str, Any]], language: str = "en", document_type: Optional[str] = None) -> DocumentSummaryResponse:
    """Create a structured, source-grounded summary with Sarvam or a local fallback."""
    if not chunks:
        return generate_fallback_summary(document_id, chunks, language)

    if not sarvam_client.api_key:
        return generate_fallback_summary(document_id, chunks, language)

    context = "\n\n".join(
        f"[Page {c.get('page_number', 1)} | {c.get('clause_label', 'Untitled section')}]\n{redact_pii(c.get('text', ''))}"
        for c in chunks[:18]
    )
    target_language = "Hindi in Devanagari" if language.lower() in {"hi", "hindi"} else "English"
    result = sarvam_client.complete_json(f"""
Summarise the financial document in {target_language}. Use only explicit facts in SOURCE; never infer missing facts.
If a category has no evidence, return []. Every bullet must end with `(Page N)` from SOURCE.
Return exactly: {{"coverage":[string],"exclusions":[string],"key_fees":[string],"waiting_periods":[string],"notable_terms":[string]}}
SOURCE:
{context}
""")
    fields = ("coverage", "exclusions", "key_fees", "waiting_periods", "notable_terms")
    if not all(isinstance(result.get(field, []), list) for field in fields):
        raise SarvamUnavailableError("Sarvam summary response did not match the expected schema.")
    return DocumentSummaryResponse(
        id=f"sum_{uuid.uuid4().hex[:12]}", document_id=document_id, language=language,
        coverage=[str(v) for v in result["coverage"]], exclusions=[str(v) for v in result["exclusions"]],
        key_fees=[str(v) for v in result["key_fees"]], waiting_periods=[str(v) for v in result["waiting_periods"]],
        notable_terms=[str(v) for v in result["notable_terms"]], model_version=sarvam_client.model,
        generated_at=datetime.utcnow(),
    )
