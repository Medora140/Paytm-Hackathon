from fastapi import APIRouter, status
from app.schemas import SessionRequest, SessionResponse, PlanTier

router = APIRouter(prefix="/auth", tags=["Auth Service"])


@router.post("/session", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def validate_or_refresh_session(payload: SessionRequest) -> SessionResponse:
    """
    Validate or refresh a Supabase/Clerk user session.
    Stub endpoint returning mock user profile and session state.
    """
    return SessionResponse(
        user_id="usr_0191eb5a-73d8-7910-b9df-20cb558b9190",
        email="demo.user@moneydocs.dev",
        plan_tier=PlanTier.FREE,
        preferred_language="en",
        is_active=True,
        session_token="mock-session-token-valid-24h"
    )
