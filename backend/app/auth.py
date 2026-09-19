import logging
import os
from typing import Any, Dict, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.db import get_db

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency that extracts and validates the Supabase access token (JWT)
    from the Authorization: Bearer <token> header.
    
    Verifies token directly with Supabase Auth:
    - If token is missing, invalid, or expired -> raises HTTP 401 Unauthorized.
    - Synchronizes/ensures user row exists in public.users table for FK integrity.
    - Never trusts any client-supplied user_id.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or empty authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials.strip()

    db = get_db()
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable.",
        )

    try:
        user_response = db.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = user_response.user
        user_id = str(user.id)
        email = user.email or ""

        # Ensure user row exists in public.users table
        try:
            db.table("users").upsert({
                "id": user_id,
                "email": email,
                "plan_tier": "free",
                "preferred_language": "en",
            }, on_conflict="id").execute()
        except Exception as e:
            logger.warning("Error syncing user %s to public.users: %s", user_id, e)

        return {
            "id": user_id,
            "email": email,
            "user_metadata": user.user_metadata or {},
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Token verification failed: %s: %s", type(e).__name__, e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication token verification failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
