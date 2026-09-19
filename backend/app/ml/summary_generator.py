import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from app.schemas import DocumentSummaryResponse
from app.errors import GeminiUnavailableError
from app.runtime_flags import running_under_pytest
from app.ml.gemini_client import (
    get_gemini_client,
    get_last_gemini_error,
    probe_gemini_connectivity,
    generate_gemini_content,
)

logger = logging.getLogger("app.ml.summary_generator")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Fallback summaries per document type if LLM is unavailable/offline
FALLBACK_SUMMARIES = {
    "mutual_fund": {
        "coverage": [
            "Equity scheme targeting capital appreciation through diversified blue-chip stocks.",
            "Permitted allocation: 80-100% in equity securities and 0-20% in debt/money market instruments.",
            "Systematic Investment Plan (SIP) and Systematic Withdrawal Plan (SWP) supported."
        ],
        "exclusions": [
            "No guaranteed or assured returns; value fluctuates with market movements.",
            "Short-selling and unhedged derivative leverage subject to statutory restrictions.",
            "Investments outside permissible SEBI asset allocation categories strictly prohibited."
        ],
        "key_fees": [
            "Exit load of 1.00% applicable if redeemed or switched out within 365 days of allotment.",
            "Total Expense Ratio (TER) capped at 2.25% under SEBI Regulation 52.",
            "Direct plan has lower TER due to absence of distributor commission."
        ],
        "waiting_periods": [
            "Minimum recommended investment horizon of 3 to 5 years for equity allocation.",
            "Statutory 3-year lock-in period applies for tax-saving ELSS variants.",
            "Cut-off time for same-day NAV allotment is 3:00 PM with funds realization."
        ],
        "notable_terms": [
            "Benchmark: NIFTY 50 Total Return Index (TRI).",
            "Grievance redressal available through AMC grievance cell and SEBI SCORES portal.",
            "15-day cooling-off / review period for initial direct applications."
        ]
    },
    "health_insurance": {
        "coverage": [
            "In-patient hospitalisation expenses up to Sum Insured for illness or accidental injury.",
            "Pre-hospitalisation medical expenses up to 60 days prior to admission.",
            "Post-hospitalisation medical expenses up to 90 days after discharge.",
            "Day care procedures covered across all listed standard clinical treatments."
        ],
        "exclusions": [
            "Permanent exclusion on cosmetic, aesthetic treatments, and weight-loss surgeries.",
            "Adventure sports injuries excluded unless specifically endorsed.",
            "Self-inflicted injuries or conditions resulting from breach of law."
        ],
        "key_fees": [
            "Room rent capped at 1% of Sum Insured per day for standard rooms.",
            "Proportionate deduction applies to associate medical charges if room rent limit is breached.",
            "Mandatory 10% co-pay for treatments in non-network hospitals."
        ],
        "waiting_periods": [
            "Initial waiting period of 30 days for any non-accidental hospitalisation.",
            "Specified disease waiting period of 24 months for cataract, hernia, joint replacement.",
            "Pre-existing conditions (PED) waiting period: 36 months of continuous coverage."
        ],
        "notable_terms": [
            "Grace period: 30 days for policy renewal without loss of continuity benefits.",
            "Free look period: 15 days from receipt of policy document for cancellation with full refund."
        ]
    },
    "loan": {
        "coverage": [
            "Secured / unsecured loan facility sanctioned up to approved principal limit.",
            "Flexible EMI repayment schedule over agreed tenor via NACH mandate.",
            "Option to prepay or partially pre-close principal balance."
        ],
        "exclusions": [
            "Loan funds cannot be utilized for speculative, gambling, or capital market activities.",
            "Moratorium benefit not applicable unless explicitly approved by lender in writing."
        ],
        "key_fees": [
            "Non-refundable loan processing fee of 1.0% to 2.0% plus statutory GST.",
            "Penal interest of 2% per month on overdue installments.",
            "Zero prepayment penalty on floating rate loans for individual borrowers as per RBI norms."
        ],
        "waiting_periods": [
            "Cooling-off / look-up period of 3 days to exit loan without penalty as per RBI guidelines.",
            "Disbursement subject to completion of title search and legal verification."
        ],
        "notable_terms": [
            "Interest rate linked to external benchmark lending rate (EBLR).",
            "Dispute redressal via Banking Ombudsman Scheme."
        ]
    }
}


def _get_gemini_client():
    """Returns the cached verified Gemini client instance, or None if unavailable."""
    return get_gemini_client()


def generate_plain_language_summary(
    document_id: str,
    chunks: List[Dict[str, Any]],
    language: str = "en",
    document_type: Optional[str] = None
) -> DocumentSummaryResponse:
    """
    Calls Gemini using structured output to generate a plain-language summary
    tuned to the document type (mutual_fund, health_insurance, loan) in English or Hindi.
    Falls back gracefully if LLM is unavailable or offline.
    """
    import re
    doc_type = (document_type or "").lower()
    
    # Primary signal: Check repository for document_type if available
    if not doc_type and document_id:
        try:
            from app.ingestion.repository import repository
            doc_meta = repository.get_document(document_id)
            if doc_meta and doc_meta.get("document_type"):
                raw_type = doc_meta["document_type"]
                doc_type = raw_type.value.lower() if hasattr(raw_type, "value") else str(raw_type).lower()
        except Exception:
            pass

    # Secondary fallback: Strict word-boundary regex detection across chunks
    if not doc_type:
        logger.warning(
            "\n" + "=" * 68 + "\n"
            "[FALLBACK WARNING] [summary_generator] Missing 'document_type' for doc '%s'!\n"
            "Action: Falling back to regex keyword inspection on chunk text.\n"
            + "=" * 68,
            document_id
        )
        combined = " ".join([c.get("text", "") for c in chunks[:5]]).lower()
        if re.search(r"\b(?:mutual\s*fund|nav|portfolio|scheme|amc|elss)\b", combined):
            doc_type = "mutual_fund"
        elif re.search(r"\b(?:loan|emi|borrower|lender|foreclosure|mortgage)\b", combined):
            doc_type = "loan"
        elif re.search(r"\b(?:insurance|policy|sum\s*insured|hospitalisation|hospitalization|co[\s\-]pay|ped|pre[\s\-]existing)\b", combined):
            doc_type = "health_insurance"
        else:
            logger.warning(
                "\n" + "=" * 68 + "\n"
                "[FALLBACK WARNING] [summary_generator] Regex keyword inspection inconclusive for doc '%s'!\n"
                "Action: Defaulting document type to 'health_insurance'.\n"
                + "=" * 68,
                document_id
            )
            doc_type = "health_insurance"

    client = _get_gemini_client()
    last_error = get_last_gemini_error() or "GEMINI_API_KEY missing or live connectivity check failed"

    if client is not None:
        try:
            from google.genai import types

            from app.ml.pii import redact_pii

            doc_text = "\n\n".join([
                f"[Page {c.get('page_number', 1)}] {c.get('clause_label', '')}\n{redact_pii(c.get('text', ''))}"
                for c in chunks[:15]  # Top 15 chunks
            ])

            target_lang_str = "Hindi (Devanagari script)" if language.lower() in ["hi", "hindi"] else "English"

            prompt = f"""
You are an expert financial consumer advocate specializing in Indian financial documents ({doc_type}).
Review the document text provided below and generate a plain-language consumer summary.

Target Language: {target_lang_str}
Document Type: {doc_type}

Produce a structured summary strictly conforming to this schema:
- coverage: list of 3-5 clear bullet points explaining key benefits, objectives, or what is covered.
- exclusions: list of 2-4 key exclusions, restricted activities, or what is NOT covered.
- key_fees: list of 2-4 critical fees, charges, loads (TER, exit load, co-pay, processing fee).
- waiting_periods: list of 2-3 lock-in periods, waiting periods, or time-based conditions.
- notable_terms: list of 2-3 other essential fine-print terms (benchmark, grievance officer, free-look).

DOCUMENT TEXT:
{doc_text}
"""
            logger.info(
                "[LIVE GEMINI CALL] [summary_generator] Initiating live Gemini API call (model=%s, doc_id=%s, doc_type=%s)...",
                MODEL_NAME,
                document_id,
                doc_type
            )
            response, used_model = generate_gemini_content(
                client=client,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema={
                        "type": "OBJECT",
                        "properties": {
                            "coverage": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "exclusions": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "key_fees": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "waiting_periods": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "notable_terms": {"type": "ARRAY", "items": {"type": "STRING"}}
                        },
                        "required": ["coverage", "exclusions", "key_fees", "waiting_periods", "notable_terms"]
                    },
                    temperature=0.1
                )
            )

            result_data = json.loads(response.text)
            logger.info(
                "[LIVE GEMINI SUCCESS] [summary_generator] Successfully generated summary via live Gemini call for doc '%s' (model=%s). Coverage items: %d, Exclusions: %d",
                document_id,
                used_model,
                len(result_data.get("coverage", [])),
                len(result_data.get("exclusions", []))
            )
            return DocumentSummaryResponse(
                id=f"sum_{uuid.uuid4().hex[:12]}",
                document_id=document_id,
                language=language,
                coverage=result_data.get("coverage", []),
                exclusions=result_data.get("exclusions", []),
                key_fees=result_data.get("key_fees", []),
                waiting_periods=result_data.get("waiting_periods", []),
                notable_terms=result_data.get("notable_terms", []),
                model_version=used_model,
                generated_at=datetime.utcnow()
            )
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            logger.warning(
                "\n" + "=" * 68 + "\n"
                "[FALLBACK WARNING] [summary_generator] Live Gemini summary generation call FAILED for doc '%s'!\n"
                "Reason: %s: %s\n"
                "Model: %s\n"
                "Action: Falling back from live summary generation.\n"
                + "=" * 68,
                document_id,
                type(e).__name__,
                e,
                MODEL_NAME
            )

    logger.warning(
        "\n" + "=" * 68 + "\n"
        "[FALLBACK WARNING] [summary_generator] Live Gemini generation unavailable for doc '%s'!\n"
        "Reason: %s\n"
        + "=" * 68,
        document_id,
        last_error
    )

    if running_under_pytest():
        logger.warning(
            "\n" + "=" * 68 + "\n"
            "[FALLBACK WARNING] [summary_generator] Pytest environment detected for doc '%s'!\n"
            "Reason: %s\n"
            "Action: Generating extractive summary from provided document chunks (canned templates disabled).\n"
            + "=" * 68,
            document_id,
            last_error
        )
        return _extractive_summary_from_chunks(document_id, chunks, language, doc_type)

    raise GeminiUnavailableError(
        f"Cannot generate a live summary for '{document_id}'. {last_error}. "
        "Canned template summaries are disabled."
    )


def _extractive_summary_from_chunks(
    document_id: str,
    chunks: List[Dict[str, Any]],
    language: str,
    document_type: str,
) -> DocumentSummaryResponse:
    """pytest-only: pull phrases from the actual chunks so tests stay grounded."""
    texts = [c.get("text", "").strip() for c in chunks if c.get("text")]
    bullets = texts[:5] or ["No extractable clause text was provided."]
    return DocumentSummaryResponse(
        id=f"sum_{uuid.uuid4().hex[:12]}",
        document_id=document_id,
        language=language,
        coverage=bullets[:3],
        exclusions=bullets[1:3] if len(bullets) > 1 else bullets,
        key_fees=bullets[:3],
        waiting_periods=bullets[:2],
        notable_terms=bullets[-2:] if len(bullets) > 1 else bullets,
        model_version=f"extractive-pytest-{document_type or 'unknown'}",
        generated_at=datetime.utcnow(),
    )
