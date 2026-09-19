import os
import re
import logging
from typing import Any, Dict, List, Optional, Tuple
from app.schemas import DocumentType

logger = logging.getLogger(__name__)


class AIDocumentClassifier:
    """
    Automatic AI classifier that inspects document text, headers, and metadata
    to automatically identify the document type, language, and issuer.
    No manual category selection required by the user.
    """

    KEYWORD_SIGNALS = {
        DocumentType.HEALTH_INSURANCE: [
            "health insurance", "mediclaim", "hospitalization", "sum insured",
            "cashless", "room rent", "copayment", "co-pay", "pre-existing disease",
            "day care treatment", "waiting period", "critical illness", "opd benefit",
            "maternity coverage", "tpa", "ayush treatment", "domiciliary",
            "स्वास्थ्य बीमा", "चिकित्सा बीमा", "बीमा राशि", "अस्पताल", "कमरे का किराया",
            "प्रतीक्षा अवधि", "पूर्व-मौजूदा बीमारी", "सह-भुगतान", "कैशलेस"
        ],
        DocumentType.TERM_LIFE_INSURANCE: [
            "life insurance", "term plan", "term life", "death benefit", "sum assured",
            "nominee", "life assured", "policy term", "premium paying term", "maturity benefit",
            "surrender value", "riders", "accidental death benefit",
            "जीवन बीमा", "टर्म इंश्योरेंस", "मृत्यु लाभ", "बीमित राशि", "नामिती", "पॉलिसी अवधि"
        ],
        DocumentType.MUTUAL_FUND: [
            "mutual fund", "scheme information document", "key information memorandum",
            "asset management company", "amc", "net asset value", "nav", "exit load",
            "expense ratio", "sip", "systematic investment plan", "benchmark index",
            "portfolio", "allotment date", "fund manager",
            "म्यूचुअल फंड", "योजना सूचना", "शुद्ध परिसंपत्ति मूल्य", "व्यय अनुपात", "निवेश"
        ],
        DocumentType.LOAN_AGREEMENT: [
            "loan agreement", "sanction letter", "borrower", "lender", "principal amount",
            "rate of interest", "roi", "emi", "equated monthly installment", "repayment schedule",
            "hypothecation", "collateral", "foreclosure charges", "disbursement",
            "ऋण अनुबंध", "उधारकर्ता", "ऋणदाता", "ब्याज दर", "मासिक किस्त", "ईएमआई"
        ],
        DocumentType.CREDIT_CARD: [
            "credit card", "billing cycle", "cardholder", "minimum amount due",
            "payment due date", "annual percentage rate", "apr", "finance charge",
            "credit limit", "available credit", "reward points", "cash advance fee",
            "क्रेडिट कार्ड", "न्यूनतम देय राशि", "क्रेडिट सीमा"
        ],
        DocumentType.EMPLOYMENT_CONTRACT: [
            "employment agreement", "contract of employment", "appointment letter",
            "employee", "employer", "designation", "probation period", "notice period",
            "salary", "ctc", "remuneration", "confidentiality clause", "non-compete",
            "रोजगार अनुबंध", "नियुक्ति पत्र", "कर्मचारी", "नियोक्ता", "वेतन"
        ],
        DocumentType.RENTAL_AGREEMENT: [
            "rental agreement", "lease agreement", "tenancy agreement", "landlord",
            "tenant", "lessor", "lessee", "monthly rent", "security deposit",
            "premises", "maintenance charges", "lock-in period", "eviction",
            "किराया अनुबंध", "पट्टा अनुबंध", "किरायेदार", "मकान मालिक", "सुरक्षा जमा"
        ]
    }

    ISSUER_PATTERNS = [
        (r"\b(?:hdfc\s+ergo|hdfc\s+life|hdfc\s+bank|hdfc\s+mutual)\b", "HDFC ERGO / HDFC Life"),
        (r"\b(?:star\s+health(?:\s+and\s+allied)?)\b", "Star Health and Allied Insurance"),
        (r"\b(?:care\s+health|religare\s+health)\b", "Care Health Insurance"),
        (r"\b(?:niva\s+bupa|max\s+bupa)\b", "Niva Bupa Health Insurance"),
        (r"\b(?:icici\s+lombard|icici\s+prudential|icici\s+bank)\b", "ICICI Lombard / Prudential"),
        (r"\b(?:sbi\s+general|sbi\s+life|state\s+bank\s+of\s+india|sbi\s+mutual)\b", "State Bank of India / SBI General"),
        (r"\b(?:bajaj\s+allianz)\b", "Bajaj Allianz General Insurance"),
        (r"\b(?:tata\s+aig|tata\s+aia)\b", "Tata AIG General Insurance"),
        (r"\b(?:aditya\s+birla|sun\s+life)\b", "Aditya Birla Capital"),
        (r"\b(?:axis\s+bank|axis\s+mutual)\b", "Axis Bank"),
        (r"\b(?:kotak\s+mahindra|kotak\s+general)\b", "Kotak Mahindra Group"),
    ]

    def classify_document(
        self,
        filename: str,
        pages_data: List[Dict[str, Any]]
    ) -> Tuple[DocumentType, str, Optional[str]]:
        """
        Classifies document text and returns:
          (DocumentType, language_code, detected_issuer_name)
        """
        # Combine text from first 4 pages for classification
        sample_pages = pages_data[:4] if pages_data else []
        combined_text = filename.lower() + "\n" + "\n".join([p.get("text", "") for p in sample_pages]).lower()

        # 1. Detect language
        hindi_chars = len(re.findall(r"[\u0900-\u097F]", combined_text))
        total_alpha = len(re.findall(r"[a-zA-Z\u0900-\u097F]", combined_text)) or 1
        hindi_ratio = hindi_chars / total_alpha

        if hindi_ratio > 0.40:
            lang = "hi"
        elif hindi_ratio > 0.05:
            lang = "mixed"
        else:
            lang = "en"

        # 2. Detect issuer
        issuer = None
        for pattern, name in self.ISSUER_PATTERNS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                issuer = name
                break

        # 3. Match keyword signals per document category
        scores: Dict[DocumentType, int] = {dt: 0 for dt in self.KEYWORD_SIGNALS}

        for doc_type, keywords in self.KEYWORD_SIGNALS.items():
            for kw in keywords:
                if kw in combined_text:
                    # Header/early mentions carry double weight
                    weight = 2 if kw in filename.lower() or (sample_pages and kw in sample_pages[0].get("text", "").lower()[:600]) else 1
                    scores[doc_type] += weight

        best_type, max_score = max(scores.items(), key=lambda x: x[1])

        # If highest score is strong, return it; otherwise fallback to general contract or health insurance default
        if max_score >= 2:
            detected_type = best_type
        elif "insurance" in combined_text or "policy" in combined_text or "बीमा" in combined_text:
            detected_type = DocumentType.HEALTH_INSURANCE
        elif "agreement" in combined_text or "contract" in combined_text or "अनुबंध" in combined_text:
            detected_type = DocumentType.GENERAL_CONTRACT
        else:
            detected_type = DocumentType.HEALTH_INSURANCE

        logger.info(
            "Auto AI Classification for '%s': type=%s (score=%s), lang=%s, issuer=%s",
            filename, detected_type.value, max_score, lang, issuer
        )
        return detected_type, lang, issuer


classifier = AIDocumentClassifier()
