import os
from typing import Any, Optional
from dotenv import load_dotenv

load_dotenv()

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
    In-memory fallback client used when Supabase credentials
    are not yet configured or remote instance is unreachable.
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
        If 'supabase' package is installed and credentials exist and respond,
        instantiates real client. Otherwise returns safe stub client.
        """
        if self._client is not None:
            return self._client

        if self.is_configured:
            try:
                import httpx
                # Fast ping to verify credentials aren't rejected before creating client
                try:
                    resp = httpx.get(
                        f"{self.supabase_url}/rest/v1/",
                        headers={"apikey": self.supabase_key, "Authorization": f"Bearer {self.supabase_key}"},
                        timeout=1.0
                    )
                    if resp.status_code in [401, 403] or resp.status_code >= 500:
                        print(f"[WARN] Supabase credentials rejected (HTTP {resp.status_code}). Using fallback.")
                        self._client = StubSupabaseClient(self.supabase_url)
                        return self._client
                except Exception:
                    print("[WARN] Supabase unreachable. Using fallback stub client.")
                    self._client = StubSupabaseClient(self.supabase_url)
                    return self._client

                from supabase import create_client, Client
                self._client = create_client(self.supabase_url, self.supabase_key)
                return self._client
            except ImportError:
                pass
            except Exception as e:
                print(f"[WARN] Failed to initialize Supabase client: {e}")

        self._client = StubSupabaseClient(self.supabase_url)
        return self._client


# Global shared singleton instance
db_helper = SupabaseConnectionHelper()


def get_db() -> Any:
    """Dependency helper to get the shared Supabase client."""
    return db_helper.get_client()
