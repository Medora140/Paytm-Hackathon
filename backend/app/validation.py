import uuid
from typing import Any

def is_valid_uuid(val: Any) -> bool:
    """
    Validates whether a given value is a well-formed RFC 4122 UUID string.
    Protects PostgreSQL/pgvector queries from throwing type syntax errors (code 22P02).
    """
    if not val or not isinstance(val, str):
        return False
    try:
        clean_val = val.strip()
        parsed = uuid.UUID(clean_val)
        return str(parsed).lower() == clean_val.lower()
    except (ValueError, AttributeError, TypeError):
        return False
