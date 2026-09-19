import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.errors import SarvamUnavailableError
from app.ml.pii import redact_pii
from app.ml.sarvam_client import sarvam_client
from app.schemas import DocumentSummaryResponse


def generate_plain_language_summary(document_id: str, chunks: List[Dict[str, Any]], language: str = "en", document_type: Optional[str] = None) -> DocumentSummaryResponse:
    """Create a structured, source-grounded summary with Sarvam."""
    if not chunks:
        raise SarvamUnavailableError("The document has no extracted text to summarise.")
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
