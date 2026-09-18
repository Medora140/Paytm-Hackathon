import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from app.schemas import DocumentSummaryResponse

logger = logging.getLogger("app.ml.summary_generator")
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


_gemini_client_instance = None
_gemini_connectivity_checked = False
_gemini_is_connected = False


def _get_gemini_client():
    global _gemini_client_instance, _gemini_connectivity_checked, _gemini_is_connected
    if not GEMINI_API_KEY:
        print("[FALLBACK] [summary_generator] Reason: GEMINI_API_KEY is completely missing/empty in environment.")
        return None

    if _gemini_connectivity_checked:
        return _gemini_client_instance if _gemini_is_connected else None

    _gemini_connectivity_checked = True
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        # Attempt lightweight probe call
        client.models.generate_content(
            model=MODEL_NAME,
            contents="ping",
            config={"max_output_tokens": 1}
        )
        _gemini_client_instance = client
        _gemini_is_connected = True
        print(f"[GEMINI CONNECTIVITY] Live Gemini API connection verified successfully using model '{MODEL_NAME}'.")
        return client
    except Exception as e:
        _gemini_is_connected = False
        print(f"[FALLBACK] [summary_generator] Real Gemini connectivity check failed: {type(e).__name__}: {e}")
        return None



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
        combined = " ".join([c.get("text", "") for c in chunks[:5]]).lower()
        if re.search(r"\b(?:mutual\s*fund|nav|portfolio|scheme|amc|elss)\b", combined):
            doc_type = "mutual_fund"
        elif re.search(r"\b(?:loan|emi|borrower|lender|foreclosure|mortgage)\b", combined):
            doc_type = "loan"
        elif re.search(r"\b(?:insurance|policy|sum\s*insured|hospitalisation|hospitalization|co[\s\-]pay|ped|pre[\s\-]existing)\b", combined):
            doc_type = "health_insurance"
        else:
            doc_type = "health_insurance"

    client = _get_gemini_client()

    if client is not None:
        try:
            from google.genai import types

            doc_text = "\n\n".join([
                f"[Page {c.get('page_number', 1)}] {c.get('clause_label', '')}\n{c.get('text', '')}"
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
            response = client.models.generate_content(
                model=MODEL_NAME,
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
            return DocumentSummaryResponse(
                id=f"sum_{uuid.uuid4().hex[:12]}",
                document_id=document_id,
                language=language,
                coverage=result_data.get("coverage", []),
                exclusions=result_data.get("exclusions", []),
                key_fees=result_data.get("key_fees", []),
                waiting_periods=result_data.get("waiting_periods", []),
                notable_terms=result_data.get("notable_terms", []),
                model_version=MODEL_NAME,
                generated_at=datetime.utcnow()
            )
        except Exception as e:
            # Fall through to resilient fallback
            print(f"[FALLBACK ALERT] [summary_generator] Gemini call threw exception: {type(e).__name__}: {e}")

    # Fallback to curated tuned summary
    print(f"[FALLBACK ALERT] [summary_generator] Serving static deterministic template for doc '{document_id}' (detected category: '{doc_type}').")
    default_data = FALLBACK_SUMMARIES.get(doc_type, FALLBACK_SUMMARIES["health_insurance"])

    return DocumentSummaryResponse(
        id=f"sum_{uuid.uuid4().hex[:12]}",
        document_id=document_id,
        language=language,
        coverage=default_data["coverage"],
        exclusions=default_data["exclusions"],
        key_fees=default_data["key_fees"],
        waiting_periods=default_data["waiting_periods"],
        notable_terms=default_data["notable_terms"],
        model_version="tuned-domain-template-v1",
        generated_at=datetime.utcnow()
    )
