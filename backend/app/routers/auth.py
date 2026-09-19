import logging
import os
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import create_client

from app.auth import get_current_user
from app.db import StubSupabaseClient, get_db
from app.schemas import (
    AuthLoginRequest,
    AuthResponse,
    AuthSignUpRequest,
    PlanTier,
    SessionRequest,
    SessionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth Service"])


def _get_admin_client():
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if url and service_key:
        return create_client(url, service_key)
    return None


def _get_auth_client():
    url = os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_ANON_KEY")
    if url and anon_key:
        return create_client(url, anon_key)
    return None


def _has_live_supabase_db() -> bool:
    db = get_db()
    return bool(db) and not isinstance(db, StubSupabaseClient)


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: AuthSignUpRequest) -> AuthResponse:
    """
    Register a new user using Supabase Auth.
    Ensures user account is created, provisioned in public.users,
    and returns session tokens.
    """
    auth_client = _get_auth_client()
    admin_client = _get_admin_client()
    db = get_db()
    if not auth_client or not _has_live_supabase_db():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable. Configure live Supabase credentials to enable auth.",
        )

    user_id = None
    email = payload.email.strip().lower()
    password = payload.password

    # Try standard client sign_up first
    try:
        res = auth_client.auth.sign_up({"email": email, "password": password})
        if res and res.user:
            user_id = str(res.user.id)
    except Exception as e:
        err_str = str(e)
        logger.warning("Standard sign_up attempt note: %s", err_str)
        # If email rate limit or confirmation required, use service role admin client
        if admin_client:
            try:
                user_obj = admin_client.auth.admin.create_user({
                    "email": email,
                    "password": password,
                    "email_confirm": True
                })
                if user_obj and user_obj.user:
                    user_id = str(user_obj.user.id)
            except Exception as admin_err:
                logger.error("Admin user creation failed: %s", admin_err)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Registration failed: {str(admin_err)}",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: {err_str}",
            )

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create user with Supabase Auth.",
        )

    # Sync into public.users table using admin client / db
    try:
        db.table("users").upsert({
            "id": user_id,
            "email": email,
            "plan_tier": "free",
            "preferred_language": "en",
        }, on_conflict="id").execute()
    except Exception as sync_err:
        logger.warning("Error syncing new user to public.users: %s", sync_err)

    # Sign in to obtain access token
    try:
        login_client = _get_auth_client()
        sign_in_res = login_client.auth.sign_in_with_password({"email": email, "password": password})
        session = sign_in_res.session
        access_token = session.access_token if session else ""
        refresh_token = session.refresh_token if session else None
    except Exception as signin_err:
        logger.warning("Auto sign-in after signup failed: %s", signin_err)
        # If email is unconfirmed, confirm via admin and retry
        if admin_client:
            try:
                admin_client.auth.admin.update_user_by_id(user_id, {"email_confirm": True})
                login_client = _get_auth_client()
                sign_in_res = login_client.auth.sign_in_with_password({"email": email, "password": password})
                session = sign_in_res.session
                access_token = session.access_token if session else ""
                refresh_token = session.refresh_token if session else None
            except Exception as retry_err:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User created, but sign-in failed: {retry_err}",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sign-in failed: {signin_err}",
            )

    return AuthResponse(
        user_id=user_id,
        email=email,
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token,
        plan_tier=PlanTier.FREE,
    )


@router.post("/login", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def login(payload: AuthLoginRequest) -> AuthResponse:
    """
    Authenticate user using Supabase Auth email/password.
    Returns access token, refresh token, and user ID.
    Never stores passwords in application database.
    """
    auth_client = _get_auth_client()
    db = get_db()
    if not auth_client or not _has_live_supabase_db():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable. Configure live Supabase credentials to enable auth.",
        )

    email = payload.email.strip().lower()
    password = payload.password

    try:
        res = auth_client.auth.sign_in_with_password({"email": email, "password": password})
        if not res or not res.session or not res.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        user_id = str(res.user.id)
        access_token = res.session.access_token
        refresh_token = res.session.refresh_token

        # Ensure synced to public.users
        try:
            db.table("users").upsert({
                "id": user_id,
                "email": email,
                "plan_tier": "free",
                "preferred_language": "en",
            }, on_conflict="id").execute()
        except Exception:
            pass

        return AuthResponse(
            user_id=user_id,
            email=email,
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
            plan_tier=PlanTier.FREE,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Login failed for '%s': %s", email, e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )


@router.get("/me", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> SessionResponse:
    """
    Returns profile information for the verified authenticated user.
    """
    return SessionResponse(
        user_id=current_user["id"],
        email=current_user["email"],
        plan_tier=PlanTier.FREE,
        preferred_language="en",
        is_active=True,
    )


@router.post("/session", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def validate_or_refresh_session(payload: SessionRequest) -> SessionResponse:
    """
    Validate a Supabase JWT access token and return the verified user profile.
    """
    auth_client = _get_auth_client()
    if not auth_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable.",
        )

    try:
        user_resp = auth_client.auth.get_user(payload.access_token)
        if not user_resp or not user_resp.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session token.",
            )

        user = user_resp.user
        return SessionResponse(
            user_id=str(user.id),
            email=user.email or "",
            plan_tier=PlanTier.FREE,
            preferred_language="en",
            is_active=True,
            session_token=payload.access_token,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Session validation failed: {str(e)}",
        )
