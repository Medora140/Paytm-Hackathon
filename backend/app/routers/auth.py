from fastapi import APIRouter, status
from app.identity import DEMO_USER_EMAIL, DEMO_USER_ID
from app.schemas import SessionRequest, SessionResponse, PlanTier

router = APIRouter(prefix="/auth", tags=["Auth Service"])


@router.post("/session", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def validate_or_refresh_session(payload: SessionRequest) -> SessionResponse:
    """
    Validate or refresh a Supabase/Clerk user session.
    Stub endpoint returning mock user profile and session state.
    """
    return SessionResponse(
        user_id=DEMO_USER_ID,
        email=DEMO_USER_EMAIL,
        plan_tier=PlanTier.FREE,
        preferred_language="en",
        is_active=True,
        session_token="mock-session-token-valid-24h"
    )
