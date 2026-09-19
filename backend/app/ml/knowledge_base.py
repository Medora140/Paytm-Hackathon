from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from app.schemas import SeverityLevel


@dataclass
class RedFlagPattern:
    pattern_id: str
    category: str  # "mutual_fund", "insurance", "lending"
    clause_type: str  # "exit_load", "expense_ratio", "room_rent_cap", etc.
    trigger_keywords: List[str]
    trigger_regex: Optional[str]
    plain_explanation_template: str
    severity_default: SeverityLevel
    source_reference: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


STARTER_KNOWLEDGE_BASE: List[RedFlagPattern] = [
    # -------------------------------------------------------------
    # Mutual Fund / Wealth Management Patterns
    # -------------------------------------------------------------
    RedFlagPattern(
        pattern_id="pat_mf_exit_load_01",
        category="mutual_fund",
        clause_type="exit_load",
        trigger_keywords=[
            "exit load", "redemption charge", "contingent deferred sales charge",
            "redemption fee", "liquidated before", "allotment of units", "exit load of"
        ],
        trigger_regex=r"(?i)\b(?:exit\s*load|redemption\s*(?:fee|charge))\b.*?(?:\d+(?:\.\d+)?\s*%|\b(?:days|months|year|days\s*from\s*allotment)\b)",
        plain_explanation_template="Exit loads penalize early liquidity by deducting up to 1-3% if units are redeemed or switched out before the specified holding window (commonly 30 to 365 days).",
        severity_default=SeverityLevel.HIGH,
        source_reference="SEBI Mutual Fund Regulations (Regulation 49 & Master Circulars on Exit Loads)"
    ),
    RedFlagPattern(
        pattern_id="pat_mf_expense_ratio_02",
        category="mutual_fund",
        clause_type="expense_ratio",
        trigger_keywords=[
            "total expense ratio", "ter limit", "management fee",
            "recurring expense", "scheme expense", "investment management fees",
            "statutory levy", "goods and services tax on management fees"
        ],
        trigger_regex=r"(?i)\b(?:total\s*expense\s*ratio|ter|recurring\s*expenses?|scheme\s*expenses?)\b.*?(?:\d+(?:\.\d+)?\s*%|\blimits?\b)",
        plain_explanation_template="High ongoing recurring expenses (TER) compound over time, heavily reducing investor net alpha and net realized returns compared to direct low-cost index benchmarks.",
        severity_default=SeverityLevel.MEDIUM,
        source_reference="SEBI (Mutual Funds) Regulations, 1996 - Regulation 52 (TER Caps)"
    ),
    RedFlagPattern(
        pattern_id="pat_mf_lockin_03",
        category="mutual_fund",
        clause_type="lock_in_period",
        trigger_keywords=[
            "lock-in period", "lock in period", "statutory lock-in", "elss lock-in",
            "cannot be redeemed", "repurchase restriction", "closed ended scheme"
        ],
        trigger_regex=r"(?i)\b(?:lock[\s\-]in\s*(?:period)?|statutory\s*lock[\s\-]in)\b.*?(?:\d+\s*(?:years?|months?))?",
        plain_explanation_template="Mandatory lock-in prevents any early redemption or emergency liquidity until the completion of the statutory timeframe (e.g. 3 years for ELSS).",
        severity_default=SeverityLevel.MEDIUM,
        source_reference="Income Tax Act, 1961 - Section 80C & SEBI ELSS Guidelines"
    ),
    RedFlagPattern(
        pattern_id="pat_mf_nav_cutoff_04",
        category="mutual_fund",
        clause_type="nav_cutoff",
        trigger_keywords=[
            "cut-off time", "cut off timing", "nav applicability",
            "closing nav of the day", "realisation of funds", "allotment of units"
        ],
        trigger_regex=r"(?i)\b(?:cut[\s\-]off\s*tim(?:e|ing)s?|nav\s*applicability)\b",
        plain_explanation_template="Strict cut-off timings and fund realization clauses delay NAV allotment to subsequent business days, risking market timing variance during volatility.",
        severity_default=SeverityLevel.LOW,
        source_reference="SEBI Circular on Uniformity in Cut-Off Timings for Mutual Fund Transactions"
    ),

    # -------------------------------------------------------------
    # Health Insurance Patterns (IRDAI / Insurance Ombudsman)
    # -------------------------------------------------------------
    RedFlagPattern(
        pattern_id="pat_irda_room_rent_01",
        category="insurance",
        clause_type="room_rent_cap",
        trigger_keywords=[
            "room rent", "room charges", "proportionate deduction",
            "icu charges limit", "standard room", "sub-limit on room"
        ],
        trigger_regex=r"(?i)\b(?:room\s*rent|room\s*charges)\b.*?(?:\d+\s*%|proportionate\s*deduction)",
        plain_explanation_template="Room rent sub-limits trigger proportionate deduction across your entire hospital bill (surgeon fees, ICU, investigations), frequently causing 30-50% surprise out-of-pocket costs.",
        severity_default=SeverityLevel.HIGH,
        source_reference="Insurance Ombudsman Award Analysis / IRDAI Health Regulations"
    ),
    RedFlagPattern(
        pattern_id="pat_irda_ped_waiting_02",
        category="insurance",
        clause_type="pre_existing_exclusion",
        trigger_keywords=[
            "waiting period", "pre-existing", "ped", "pre existing disease",
            "continuous coverage", "declared or undeclared"
        ],
        trigger_regex=r"(?i)\b(?:pre[\s\-]existing\s*(?:diseases?|conditions?|ailments?)|ped)\b.*?(?:\d+\s*(?:months?|years?))?",
        plain_explanation_template="Extended pre-existing disease waiting periods (36-48 months) are the primary driver of early claim repudiations before insurance ombudsman panels.",
        severity_default=SeverityLevel.MEDIUM,
        source_reference="IRDAI Master Circular on Standardization of Health Insurance Contracts"
    ),
    RedFlagPattern(
        pattern_id="pat_irda_copay_03",
        category="insurance",
        clause_type="co_payment",
        trigger_keywords=[
            "co-pay", "copayment", "co-payment", "mandatory co-pay",
            "non-network hospital", "proportionate share"
        ],
        trigger_regex=r"(?i)\b(?:co[\s\-]pay(?:ment)?)\b.*?(?:\d+\s*%)?",
        plain_explanation_template="Mandatory co-payment mandates that the insured bear 10-20% of every approved claim out-of-pocket, even at network hospitals.",
        severity_default=SeverityLevel.LOW,
        source_reference="IRDAI Guidelines on Co-payment Clauses"
    ),
    RedFlagPattern(
        pattern_id="pat_irda_specific_illness_04",
        category="insurance",
        clause_type="specific_illness_waiting",
        trigger_keywords=[
            "cataract", "hernia", "joint replacement", "24 months waiting",
            "two year exclusion", "specified disease waiting period"
        ],
        trigger_regex=r"(?i)\b(?:cataract|hernia|joint\s*replacement|stones?)\b.*?(?:\d+\s*(?:months?|years?)\s*waiting)",
        plain_explanation_template="Specific common medical conditions are excluded during the initial 12 to 24 months of coverage regardless of pre-existence.",
        severity_default=SeverityLevel.LOW,
        source_reference="IRDAI Standardization Clauses"
    ),

    # -------------------------------------------------------------
    # Lending / Loan Patterns (RBI Ombudsman)
    # -------------------------------------------------------------
    RedFlagPattern(
        pattern_id="pat_rbi_prepayment_01",
        category="lending",
        clause_type="prepayment_penalty",
        trigger_keywords=[
            "prepayment penalty", "foreclosure charges", "early repayment",
            "pre-payment fee", "foreclosure penalty"
        ],
        trigger_regex=r"(?i)\b(?:pre[\s\-]payment\s*(?:penalty|charges?)|foreclosure\s*charges?)\b",
        plain_explanation_template="Prepayment penalties restrict borrowers from refinancing or repaying debt early, conflicting with RBI consumer protection directives on floating rate loans.",
        severity_default=SeverityLevel.HIGH,
        source_reference="RBI Master Direction on Consumer Loans and Prepayment Charges"
    ),
    RedFlagPattern(
        pattern_id="pat_rbi_proc_fee_02",
        category="lending",
        clause_type="processing_fee",
        trigger_keywords=[
            "processing fee", "administrative charge", "non-refundable fee",
            "upfront charges", "loan login fee"
        ],
        trigger_regex=r"(?i)\b(?:processing\s*fee|administrative\s*charge)\b.*?(?:non[\s\-]refundable)",
        plain_explanation_template="Non-refundable processing charges are retained by the lender even if the loan application is rejected or not disbursed.",
        severity_default=SeverityLevel.LOW,
        source_reference="RBI Fair Practices Code for Lenders"
    ),
]


class RedFlagKnowledgeBase:
    """
    Knowledge base interface providing pattern lookup, search, and categorization.
    Dynamically loads patterns from Supabase red_flag_patterns table,
    with transparent fallback to STARTER_KNOWLEDGE_BASE.
    """

    def __init__(self, patterns: Optional[List[RedFlagPattern]] = None):
        if patterns is not None:
            self._patterns = list(patterns)
        else:
            self._patterns = self._load_patterns()

    def _load_patterns(self) -> List[RedFlagPattern]:
        try:
            from app.db import get_db, StubSupabaseClient
            db = get_db()
            if not isinstance(db, StubSupabaseClient) and db.__class__.__name__ != "StubSupabaseClient":
                res = db.table("red_flag_patterns").select("*").execute()
                if hasattr(res, "data") and res.data:
                    loaded = []
                    for row in res.data:
                        sev_str = row.get("severity_default", "medium").lower()
                        try:
                            sev = SeverityLevel(sev_str)
                        except Exception:
                            sev = SeverityLevel.MEDIUM
                        
                        # Find original starter pattern if ID matches or clause_type matches
                        orig_id = row.get("id")
                        for sp in STARTER_KNOWLEDGE_BASE:
                            import uuid
                            if str(uuid.uuid5(uuid.NAMESPACE_DNS, sp.pattern_id)) == str(orig_id):
                                orig_id = sp.pattern_id
                                break

                        loaded.append(
                            RedFlagPattern(
                                pattern_id=str(orig_id),
                                category=row.get("category", "general"),
                                clause_type=row.get("clause_type", "general"),
                                trigger_keywords=row.get("trigger_keywords", []) or [],
                                trigger_regex=row.get("trigger_regex"),
                                plain_explanation_template=row.get("plain_explanation_template", ""),
                                severity_default=sev,
                                source_reference=row.get("source_reference", "")
                            )
                        )
                    if loaded:
                        return loaded
        except Exception:
            pass
        return list(STARTER_KNOWLEDGE_BASE)

    @property
    def patterns(self) -> List[RedFlagPattern]:
        return self._patterns

    def get_patterns(self, category: Optional[str] = None) -> List[RedFlagPattern]:
        if not category:
            return self._patterns
        category_clean = category.lower().strip()
        return [p for p in self._patterns if p.category.lower() == category_clean]

    def get_pattern_by_id(self, pattern_id: str) -> Optional[RedFlagPattern]:
        for p in self._patterns:
            if p.pattern_id == pattern_id:
                return p
        return None

    def add_pattern(self, pattern: RedFlagPattern) -> None:
        self._patterns.append(pattern)

