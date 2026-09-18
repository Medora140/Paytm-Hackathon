from typing import Any, Dict, List, Optional
from app.db import get_db

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
    Retrieves document chunks.
    1. Checks repository memory cache (where Agent A ingestion stores real extracted chunks)
    2. Checks Supabase database 'document_chunks' table if available
    3. Falls back to matching mock fixtures with loud visible logging
    """
    # 1. Check repository cache first
    try:
        from app.ingestion.repository import repository
        repo_chunks = repository.get_chunks(document_id)
        if repo_chunks and len(repo_chunks) > 0:
            print(f"[CHUNK RESOLVER] Loaded {len(repo_chunks)} real extracted chunks from Ingestion Repository for doc '{document_id}'.")
            return repo_chunks
    except Exception as e:
        print(f"[CHUNK RESOLVER] Repository check failed: {e}")

    # 2. Check Supabase DB
    db = get_db()
    fallback_reason = "Unknown"
    
    if db is None:
        fallback_reason = "db client is None"
    else:
        try:
            res = db.table("document_chunks").select("*").eq("document_id", document_id).execute()
            data = res.data if hasattr(res, "data") else (res.get("data") if isinstance(res, dict) else None)
            if data and len(data) > 0:
                print(f"[CHUNK RESOLVER] Loaded {len(data)} real document_chunks from Supabase for doc '{document_id}'.")
                chunks = []
                for row in data:
                    chunks.append({
                        "id": str(row.get("id")),
                        "page_number": int(row.get("page_number", 1)),
                        "clause_label": row.get("clause_label") or f"Clause (Page {row.get('page_number', 1)})",
                        "text": row.get("text", "")
                    })
                return chunks
            else:
                fallback_reason = f"Supabase document_chunks query succeeded but returned 0 rows for doc '{document_id}'"
        except Exception as e:
            fallback_reason = f"Supabase query failed with exception: {type(e).__name__}: {e}"

    # 3. Check document metadata to select correct mock fixture if fallback is needed
    chosen_category = "health_insurance"
    try:
        from app.ingestion.repository import repository
        doc_meta = repository.get_document(document_id)
        if doc_meta and doc_meta.get("document_type"):
            raw_type = doc_meta["document_type"]
            chosen_category = raw_type.value.lower() if hasattr(raw_type, "value") else str(raw_type).lower()
    except Exception:
        pass

    doc_lower = document_id.lower()
    if chosen_category == "mutual_fund" or "mf" in doc_lower or "fund" in doc_lower or "hdfc" in doc_lower:
        chosen_fixture = "SYNTHETIC_MUTUAL_FUND_CHUNKS"
        fixture_data = list(SYNTHETIC_MUTUAL_FUND_CHUNKS)
    else:
        chosen_fixture = "MOCK_HEALTH_INSURANCE_CHUNKS (Wave 0 default)"
        fixture_data = list(MOCK_HEALTH_INSURANCE_CHUNKS)

    print(f"[FALLBACK ALERT] [chunk_resolver] Serving {chosen_fixture} ({len(fixture_data)} chunks) for doc '{document_id}'. Reason: {fallback_reason}.")
    return fixture_data


