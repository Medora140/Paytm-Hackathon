import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.db import StubSupabaseClient
from app.routers.auth import signup, login


class DummyAuthClient:
    class auth:
        @staticmethod
        def sign_up(payload):
            return SimpleNamespace(user=SimpleNamespace(id="u-123"))

        @staticmethod
        def sign_in_with_password(payload):
            return SimpleNamespace(
                session=SimpleNamespace(
                    access_token="token-123",
                    refresh_token="refresh-123",
                ),
                user=SimpleNamespace(id="u-123"),
            )


def run_async(coro):
    return asyncio.run(coro)


def test_signup_rejects_stub_supabase_when_auth_is_unavailable(monkeypatch):
    monkeypatch.setattr("app.routers.auth._get_auth_client", lambda: DummyAuthClient())
    monkeypatch.setattr("app.routers.auth._get_admin_client", lambda: None)
    monkeypatch.setattr("app.routers.auth.get_db", lambda: StubSupabaseClient("https://example.supabase.co"))

    async def _call():
        with pytest.raises(HTTPException) as exc:
            await signup(type("Payload", (), {"email": "user@example.com", "password": "secret123"})())
        assert exc.value.status_code == 503

    run_async(_call())


def test_login_rejects_stub_supabase_when_auth_is_unavailable(monkeypatch):
    monkeypatch.setattr("app.routers.auth._get_auth_client", lambda: DummyAuthClient())
    monkeypatch.setattr("app.routers.auth.get_db", lambda: StubSupabaseClient("https://example.supabase.co"))

    async def _call():
        with pytest.raises(HTTPException) as exc:
            await login(type("Payload", (), {"email": "user@example.com", "password": "secret123"})())
        assert exc.value.status_code == 503

    run_async(_call())
