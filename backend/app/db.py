import logging
import os
from typing import Any, Optional
from dotenv import load_dotenv
from app.runtime_flags import allow_in_memory_stores

load_dotenv()

logger = logging.getLogger("app.db")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")


class StubResult:
    def __init__(self, data=None):
        self.data = data or []
        self.count = len(self.data)

    def __getitem__(self, item):
        return getattr(self, item, None)


class StubSupabaseClient:
    """
    Test-only client. Production must never silently treat this as a live database.
    """
    def __init__(self, url: str):
        self.url = url

    def table(self, name: str):
        return self

    def select(self, *args, **kwargs):
        return self

    def insert(self, *args, **kwargs):
        return self

    def update(self, *args, **kwargs):
        return self

    def delete(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def execute(self):
        return StubResult()


class SupabaseConnectionHelper:
    """
    Shared Supabase and PostgreSQL connection helper.
    Contains no business logic. Exposes client initialization
    with graceful fallback for development, testing, and offline modes.
    """

    def __init__(self):
        self._client: Optional[Any] = None
        self.supabase_url: str = SUPABASE_URL
        self.supabase_key: str = SUPABASE_KEY
        self.database_url: str = DATABASE_URL

    @property
    def is_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_key and not self.supabase_key.startswith("your_"))

    def get_client(self) -> Any:
        """
        Returns an initialized Supabase client instance.
        Live credentials that fail are errors, not a silent stub database.
        """
        if self._client is not None:
            return self._client

        if self.is_configured:
            try:
                import httpx
                try:
                    resp = httpx.get(
                        f"{self.supabase_url}/rest/v1/",
                        headers={"apikey": self.supabase_key, "Authorization": f"Bearer {self.supabase_key}"},
                        timeout=5.0
                    )
                    if resp.status_code in [401, 403] or resp.status_code >= 500:
                        msg = f"Supabase credentials rejected (HTTP {resp.status_code})"
                        logger.error(msg)
                        if allow_in_memory_stores():
                            logger.error("ALLOW_IN_MEMORY_FALLBACKS/pytest is set; using StubSupabaseClient")
                            self._client = StubSupabaseClient(self.supabase_url)
                            return self._client
                        raise RuntimeError(msg)
                except RuntimeError:
                    raise
                except Exception as ping_err:
                    msg = f"Supabase unreachable during health ping: {type(ping_err).__name__}: {ping_err}"
                    logger.error(msg)
                    if allow_in_memory_stores():
                        logger.error("ALLOW_IN_MEMORY_FALLBACKS/pytest is set; using StubSupabaseClient")
                        self._client = StubSupabaseClient(self.supabase_url)
                        return self._client
                    raise RuntimeError(msg) from ping_err

                from supabase import create_client
                self._client = create_client(self.supabase_url, self.supabase_key)
                logger.info("Live Supabase client initialized for %s", self.supabase_url)
                return self._client
            except RuntimeError:
                raise
            except ImportError:
                logger.error("supabase package is not installed")
            except Exception as e:
                logger.error("Failed to initialize Supabase client: %s", e)
                if not allow_in_memory_stores():
                    raise

        if allow_in_memory_stores():
            logger.error(
                "Supabase is not configured. Using StubSupabaseClient because tests/ALLOW_IN_MEMORY_FALLBACKS=1."
            )
            self._client = StubSupabaseClient(self.supabase_url)
            return self._client

        raise RuntimeError(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
            "(or SUPABASE_ANON_KEY). Silent stub databases are disabled."
        )


# Global shared singleton instance
db_helper = SupabaseConnectionHelper()


def get_db() -> Any:
    """Dependency helper to get the shared Supabase client."""
    return db_helper.get_client()
