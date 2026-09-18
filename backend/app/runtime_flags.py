import os
import sys


def running_under_pytest() -> bool:
    """True when a pytest session is executing the current process."""
    return bool(os.getenv("PYTEST_CURRENT_TEST")) or "pytest" in sys.modules


def allow_in_memory_stores() -> bool:
    """
    In-memory / stub stores are allowed for unit tests and explicit local opt-in.
    Production and live integration runs must talk to real Supabase.
    """
    if running_under_pytest():
        return True
    flag = os.getenv("ALLOW_IN_MEMORY_FALLBACKS", "").strip().lower()
    return flag in {"1", "true", "yes"}
