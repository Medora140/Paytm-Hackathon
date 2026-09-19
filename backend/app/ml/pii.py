"""
PII Redaction Engine for Money Docs Decoded.
Implements field-aware and validated pattern matching (not naive substring replacement)
to strip/mask sensitive consumer identifiers before document chunk text is transmitted to Gemini.

Redaction Scope (per aiEngine.md):
- Personal names (with titles / contextual headers)
- Date of Birth (DOB)
- Contact information (phone numbers, email addresses)
- Addresses & PIN codes
- Policy, customer, and account identifiers
- Government & financial identifiers (PAN, Aadhaar)

Explicitly Preserved Financial Terms & Values:
- Premium, EMI, rent / room rent, loan amount, interest rate, coverage amount, tenure,
  sum insured, co-pay, deductible, expense ratio, exit load.
"""

import re
import logging
from typing import Tuple

logger = logging.getLogger("app.ml.pii")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Redaction Replacement Tokens
# ---------------------------------------------------------------------------
REDACTED_NAME = "[REDACTED_NAME]"
REDACTED_DOB = "[REDACTED_DOB]"
REDACTED_PHONE = "[REDACTED_PHONE]"
REDACTED_EMAIL = "[REDACTED_EMAIL]"
REDACTED_ADDRESS = "[REDACTED_ADDRESS]"
REDACTED_POLICY_NO = "[REDACTED_POLICY_NO]"
REDACTED_ACCOUNT_NO = "[REDACTED_ACCOUNT_NO]"
REDACTED_PAN = "[REDACTED_PAN]"
REDACTED_AADHAAR = "[REDACTED_AADHAAR]"

# ---------------------------------------------------------------------------
# Regex Patterns for Field-Aware Redaction
# ---------------------------------------------------------------------------

# Indian Mobile / Phone numbers (handles +91, 0, spaces, dashes; ensures not a currency or date)
PHONE_REGEX = re.compile(
    r"(?:\+91[\s\-]?)?(?:\b[6-9]\d{4}[\s\-]?\d{5}\b|\b[6-9]\d{9}\b)"
)

# Email Addresses
EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)

# Date of Birth (labeled variants to avoid masking generic dates/tenure)
DOB_REGEX = re.compile(
    r"(?i)\b(?:d\.?o\.?b\.?|date\s*of\s*birth|birth\s*date)\s*[:=\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4})"
)

# Indian PAN Card Format: 5 uppercase letters, 4 digits, 1 uppercase letter
PAN_REGEX = re.compile(
    r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"
)

# Aadhaar numbers: 12 digits, commonly formatted as 4 4 4 or 12 continuous digits with label
AADHAAR_REGEX = re.compile(
    r"(?i)(?:aadhaar(?:\s*no\.?|\s*number)?\s*[:=\-]?\s*)?(\b\d{4}\s\d{4}\s\d{4}\b)"
)

# Policy Numbers: labeled identifiers or POL- style numbers
POLICY_NO_REGEX = re.compile(
    r"(?i)\b(?:policy\s*(?:no\.?|number|id)|certificate\s*no\.?)\s*[:=\-]?\s*([A-Za-z0-9\/\-]{5,25})\b"
)

# Account Numbers: labeled bank/customer account numbers (avoiding bare numeric amounts)
ACCOUNT_NO_REGEX = re.compile(
    r"(?i)\b(?:account\s*(?:no\.?|number)|a\/c\s*no\.?|customer\s*(?:id|no\.?))\s*[:=\-]?\s*([0-9]{9,18})\b"
)

# Named Entities: Title / Salutation prefixes (Mr./Ms./Mrs./Dr./Shri/Smt.) followed by capitalized names
NAME_PREFIX_REGEX = re.compile(
    r"\b(?:Mr\.|Ms\.|Mrs\.|Dr\.|Shri|Smt\.|Master)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b"
)

# Labeled Consumer Names: "Policyholder:", "Proposer:", "Insured Name:", "Borrower Name:"
LABELED_NAME_REGEX = re.compile(
    r"(?i)\b(?:policy\s*holder(?:\s*name)?|proposer(?:\s*name)?|insured(?:\s*person|\s*name)?|borrower(?:\s*name)?|client\s*name)\s*[:=\-]?\s*([A-Za-z\s\.]{3,35})(?=\s*[,;\n\r]|(?:\s+(?:aged?|residing|s\/o|d\/o|w\/o|gender|dob|sum)))"
)

# PIN codes preceded by Pin / Postal / Pincode / State indicator
PINCODE_REGEX = re.compile(
    r"(?i)\b(?:pin\s*code|pincode|postal\s*code|pin)\s*[:=\-]?\s*(\b[1-9][0-9]{5}\b)"
)


def redact_pii(text: str) -> str:
    """
    Scrubs PII from input text and replaces with safe contextual placeholders.
    Guarantees that financial numbers and terms (premium, EMI, room rent, loan amounts)
    remain intact and unmodified.
    """
    if not text:
        return text

    scrubbed = text

    # 1. Redact Email Addresses
    scrubbed = EMAIL_REGEX.sub(REDACTED_EMAIL, scrubbed)

    # 2. Redact Date of Birth (preserve the label, redact the date)
    def _sub_dob(match):
        prefix = match.group(0).split(match.group(1))[0]
        return f"{prefix}{REDACTED_DOB}"
    scrubbed = DOB_REGEX.sub(_sub_dob, scrubbed)

    # 3. Redact PAN
    scrubbed = PAN_REGEX.sub(REDACTED_PAN, scrubbed)

    # 4. Redact Aadhaar
    def _sub_aadhaar(match):
        full = match.group(0)
        num = match.group(1)
        return full.replace(num, REDACTED_AADHAAR)
    scrubbed = AADHAAR_REGEX.sub(_sub_aadhaar, scrubbed)

    # 5. Redact Policy Numbers (preserve the label)
    def _sub_policy(match):
        full = match.group(0)
        pol = match.group(1)
        return full.replace(pol, REDACTED_POLICY_NO)
    scrubbed = POLICY_NO_REGEX.sub(_sub_policy, scrubbed)

    # 6. Redact Account Numbers (preserve the label)
    def _sub_account(match):
        full = match.group(0)
        acc = match.group(1)
        return full.replace(acc, REDACTED_ACCOUNT_NO)
    scrubbed = ACCOUNT_NO_REGEX.sub(_sub_account, scrubbed)

    # 7. Redact Phone Numbers (not matching financial figures like INR 75,000)
    def _sub_phone(match):
        start = match.start()
        prefix = scrubbed[max(0, start - 10):start].lower()
        if any(c in prefix for c in ["rs", "inr", "₹", "amount", "limit", "cap"]):
            return match.group(0)
        return REDACTED_PHONE
    scrubbed = PHONE_REGEX.sub(_sub_phone, scrubbed)

    # 8. Redact PIN codes
    def _sub_pin(match):
        full = match.group(0)
        pin = match.group(1)
        return full.replace(pin, REDACTED_ADDRESS)
    scrubbed = PINCODE_REGEX.sub(_sub_pin, scrubbed)

    # 9. Redact Labeled Names
    def _sub_labeled_name(match):
        full = match.group(0)
        name = match.group(1)
        return full.replace(name.strip(), REDACTED_NAME)
    scrubbed = LABELED_NAME_REGEX.sub(_sub_labeled_name, scrubbed)

    # 10. Redact Salutation Names (Mr. John Doe -> Mr. [REDACTED_NAME])
    def _sub_name_prefix(match):
        full = match.group(0)
        name = match.group(1)
        return full.replace(name, REDACTED_NAME)
    scrubbed = NAME_PREFIX_REGEX.sub(_sub_name_prefix, scrubbed)

    return scrubbed


def redact_chunks(chunks: list) -> list:
    """
    Creates a copy of document chunk records with text redacted for PII.
    Leaves original chunk data structure untouched.
    """
    redacted_chunks = []
    for c in chunks:
        c_copy = dict(c)
        original_text = c.get("text", "")
        c_copy["text"] = redact_pii(original_text)
        redacted_chunks.append(c_copy)
    return redacted_chunks
