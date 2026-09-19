import logging
from typing import Any, Dict, List, Optional
from app.db import get_db
from app.errors import ChunksNotFoundError

logger = logging.getLogger("app.ml.chunk_resolver")

SYNTHETIC_MUTUAL_FUND_CHUNKS: List[Dict[str, Any]] = [
    {
        "id": "chk_mf_p1_obj",
        "page_number": 1,
        "clause_label": "Section 1: Scheme Objective & Asset Allocation",
        "text": (
            "The primary objective of the Scheme is to generate long-term capital appreciation by investing "
            "predominantly in equity and equity-related securities of large-cap companies. The scheme will allocate "
            "80% to 100% in Large Cap Equities and 0% to 20% in Debt and Money Market Instruments."
        )
    },
    {
        "id": "chk_mf_p2_exit_load",
        "page_number": 2,
        "clause_label": "Section 2: Exit Load & Redemption Charges",
        "text": (
            "Exit Load Structure: If units are redeemed or switched out within 365 days from the date of allotment, "
            "an exit load of 1.00% of the applicable NAV will be charged. If units are redeemed or switched out "
            "after 365 days from allotment, the exit load is NIL. Redemptions effected through Systematic Withdrawal "
            "Plans (SWP) up to 10% of initial investment within 1 year will be exempt from redemption fee."
        )
    },
    {
        "id": "chk_mf_p4_expense",
        "page_number": 4,
        "clause_label": "Section 4: Annual Scheme Expenses & Total Expense Ratio (TER)",
        "text": (
            "The Total Expense Ratio (TER) permissible under Regulation 52 includes investment management fees, "
            "custodial fees, registrar and transfer agent fees, and marketing/selling expenses. "
            "The maximum recurring expense charged to the Regular Plan shall not exceed 2.25% of daily net assets. "
            "Additionally, brokerage and transaction costs incurred for execution of trade may be charged to the scheme "
            "up to 0.12% for cash market transactions."
        )
    },
    {
        "id": "chk_mf_p5_lockin",
        "page_number": 5,
        "clause_label": "Section 5: Statutory Lock-in Period & Liquidity Terms",
        "text": (
            "In accordance with the Equity Linked Savings Scheme (ELSS) guidelines notified by the Central Government, "
            "all investments under the Tax Advantage Plan are subject to a mandatory statutory lock-in period of 3 years "
            "from the date of unit allotment. During this 3-year lock-in period, no repurchase, transfer, or redemption "
            "of units shall be permitted under any circumstances."
        )
    },
    {
        "id": "chk_mf_p7_nav",
        "page_number": 7,
        "clause_label": "Section 7: Cut-Off Timing & NAV Applicability",
        "text": (
            "Cut-off timing for subscription and redemption: For purchase applications received up to 3:00 PM along with "
            "realisation of funds into the scheme's account before 3:00 PM, the closing NAV of the day shall be applicable. "
            "If funds are received after 3:00 PM, units will be allotted based on the NAV of the next business day."
        )
    },
    {
        "id": "chk_mf_p8_grievance",
        "page_number": 8,
        "clause_label": "Section 8: Grievance Redressal Mechanism & Investor Protection",
        "text": (
            "Investors may register complaints with the AMC Investor Grievance Officer or lodge disputes through the "
            "SEBI SCORES online portal. All investor queries and complaints must be resolved within 21 business days. "
            "The Scheme provides a 15-day cooling-off review window for new direct folios."
        )
    }
]

MOCK_HEALTH_INSURANCE_CHUNKS: List[Dict[str, Any]] = [
    {
        "id": "chk_page14_sec4",
        "page_number": 14,
        "clause_label": "Clause 4.2 - Room Rent Sub-limits",
        "text": (
            "The company's liability for room charges is restricted to 1% of Sum Insured per day (up to INR 5,000/day). "
            "If the insured occupies a room with a higher rent, all associated medical expenses will be proportionately reduced."
        )
    },
    {
        "id": "chk_page18_sec9",
        "page_number": 18,
        "clause_label": "Clause 9.1 - Pre-Existing Diseases Exclusion",
        "text": (
            "Any condition declared or undeclared for which symptoms occurred within 36 months prior to inception is "
            "excluded from coverage until 36 months of continuous renewals have elapsed."
        )
    },
    {
        "id": "chk_page22_sec12",
        "page_number": 22,
        "clause_label": "Clause 12.4 - Non-Network Hospital Co-payment",
        "text": (
            "An additional co-pay of 10% shall be borne by the insured person for each and every admissible claim "
            "treated at a non-network hospital."
        )
    },
    {
        "id": "chk_page25_sec15",
        "page_number": 25,
        "clause_label": "Clause 15.1 - Grievance Redressal & Free-Look Period",
        "text": (
            "The insured has a free look period of 15 days from receipt of the policy document to review the terms. "
            "If unsatisfied, the policyholder may request cancellation with refund of premium. Complaints may be escalated "
            "to the Insurance Ombudsman."
        )
    }
]


def get_chunks_for_document(document_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves document chunks directly from the live Supabase document_chunks table.
    The in-memory repository cache is never preferred and is only consulted as a
    last-resort fallback in degraded mode (e.g. unit testing with stub clients).
    """
    from app.runtime_flags import allow_in_memory_stores
    from app.validation import is_valid_uuid

    if not is_valid_uuid(document_id):
        reason = f"Document ID '{document_id}' is not a valid UUID"
        if allow_in_memory_stores():
            try:
                from app.ingestion.repository import repository
                repo_chunks = repository._chunks.get(document_id)
                if repo_chunks and len(repo_chunks) > 0:
                    logger.warning(
                        "\n" + "=" * 68 + "\n"
                        "[DEGRADED MODE] [mock_data] Non-UUID document ID '%s' resolved via in-memory repository chunks (%d chunks).\n"
                        + "=" * 68,
                        document_id,
                        len(repo_chunks)
                    )
                    return repo_chunks
            except Exception:
                pass
        raise ChunksNotFoundError(document_id, reason)

    # 1. Primary Source: Direct Supabase document_chunks query
    db = get_db()
    if db is not None and db.__class__.__name__ != "StubSupabaseClient":
        try:
            res = (
                db.table("document_chunks")
                .select("*")
                .eq("document_id", document_id)
                .order("page_number")
                .execute()
            )
            data = res.data if hasattr(res, "data") else (res.get("data") if isinstance(res, dict) else None)
            if data and len(data) > 0:
                logger.info(
                    "Loaded %s real document_chunks from Supabase for doc '%s'.",
                    len(data),
                    document_id,
                )
                chunks = []
                for row in data:
                    chunks.append({
                        "id": str(row.get("id")),
                        "document_id": document_id,
                        "page_number": int(row.get("page_number", 1)),
                        "clause_label": row.get("clause_label") or f"Clause (Page {row.get('page_number', 1)})",
                        "text": row.get("text", ""),
                        "embedding": row.get("embedding")
                    })
                return chunks
        except Exception as e:
            logger.error("Supabase document_chunks query failed for doc '%s': %s", document_id, e)

    # 2. Last-resort fallback: only if in-memory stores are explicitly permitted
    if allow_in_memory_stores():
        try:
            from app.ingestion.repository import repository
            repo_chunks = repository._chunks.get(document_id)
            if repo_chunks and len(repo_chunks) > 0:
                logger.warning(
                    "\n" + "=" * 68 + "\n"
                    "[DEGRADED MODE] [mock_data] Supabase query returned 0 chunks or is unavailable for doc '%s'!\n"
                    "Action: Falling back to in-memory ingestion repository cache (%d chunks).\n"
                    + "=" * 68,
                    document_id,
                    len(repo_chunks)
                )
                return repo_chunks
        except Exception as e:
            logger.warning("In-memory repository fallback failed for doc '%s': %s", document_id, e)

    reason = f"No document_chunks found in Supabase for document '{document_id}'"
    logger.warning(
        "\n" + "=" * 68 + "\n"
        "[FALLBACK WARNING] [mock_data] Chunks could not be found for doc '%s'!\n"
        "Reason: %s\n"
        + "=" * 68,
        document_id,
        reason
    )
    raise ChunksNotFoundError(document_id, reason)


