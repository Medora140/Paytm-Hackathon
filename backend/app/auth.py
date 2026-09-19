import logging
import os
from typing import Any, Dict, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.db import get_db

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


GUEST_USER_ID = "00000000-0000-0000-0000-000000000000"
DEFAULT_GUEST_USER: Dict[str, Any] = {
    "id": GUEST_USER_ID,
    "email": "guest@moneydocs.local",
    "user_metadata": {"role": "guest"},
}


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency that extracts and validates the Supabase access token (JWT)
    if present, but seamlessly falls back to a guest user session so anyone can
    upload and analyze documents without login or sign up barriers.
    """
    if not credentials or not credentials.credentials:
        return DEFAULT_GUEST_USER

    token = credentials.credentials.strip()
    if not token or token == "placeholder-anon-key":
        return DEFAULT_GUEST_USER

    db = get_db()
    if not db:
        return DEFAULT_GUEST_USER

    try:
        user_response = db.auth.get_user(token)
        if not user_response or not user_response.user:
            return DEFAULT_GUEST_USER

        user = user_response.user
        user_id = str(user.id)
        email = user.email or ""

        # Ensure user row exists in public.users table if possible
        try:
            db.table("users").upsert({
                "id": user_id,
                "email": email,
                "plan_tier": "free",
                "preferred_language": "en",
            }, on_conflict="id").execute()
        except Exception as e:
            logger.debug("Non-fatal user sync to public.users: %s", e)

        return {
            "id": user_id,
            "email": email,
            "user_metadata": user.user_metadata or {},
        }
    except Exception as e:
        logger.debug("Token fallback to guest user: %s", e)
        return DEFAULT_GUEST_USER

