"""Auth endpoint tests.

Unit tests here cover unauthenticated access (no DB required).
Integration tests for register/login are marked with @pytest.mark.integration
and require a running PostgreSQL instance.
"""

import pytest


class TestUnauthenticated:
    @pytest.mark.asyncio
    async def test_chat_requires_auth(self, unauth_client):
        response = await unauth_client.post("/chat", json={"message": "Hola"})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_end_session_requires_auth(self, unauth_client):
        response = await unauth_client.post(
            "/chat/end-session", json={"session_id": "test-session"}
        )
        assert response.status_code == 401
