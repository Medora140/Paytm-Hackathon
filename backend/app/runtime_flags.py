import os
import sys


def running_under_pytest() -> bool:
    """True when a pytest session is executing the current process."""
    return bool(os.getenv("PYTEST_CURRENT_TEST")) or "pytest" in sys.modules


def allow_in_memory_stores() -> bool:
    """
    In-memory / stub stores are allowed for unit tests and local/dev mode when
    Supabase credentials are not configured. Production deployments should still
    point to real Supabase unless explicitly opting into the local fallback.
    """
    if running_under_pytest():
        return True

    has_supabase_config = bool(
        os.getenv("SUPABASE_URL")
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )
    if not has_supabase_config:
        return True

    flag = os.getenv("ALLOW_IN_MEMORY_FALLBACKS", "").strip().lower()
    return flag in {"1", "true", "yes"}
