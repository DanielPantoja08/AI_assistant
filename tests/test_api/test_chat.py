"""Chat endpoint unit tests — no database required."""

import pytest

from tests.test_api.conftest import TEST_USER_ID


class TestChatEndpoint:
    @pytest.mark.asyncio
    async def test_returns_response_and_session_id(self, client):
        response = await client.post("/chat", json={"message": "Me siento triste"})
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Entiendo cómo te sientes."
        assert data["session_id"]

    @pytest.mark.asyncio
    async def test_auto_generates_session_id(self, client):
        r1 = await client.post("/chat", json={"message": "Hola"})
        r2 = await client.post("/chat", json={"message": "Hola"})
        assert r1.json()["session_id"] != r2.json()["session_id"]

    @pytest.mark.asyncio
    async def test_uses_provided_session_id(self, client):
        session_id = "my-fixed-session"
        response = await client.post(
            "/chat", json={"message": "Hola", "session_id": session_id}
        )
        assert response.status_code == 200
        assert response.json()["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_passes_user_id_to_graph(self, client, mock_graph):
        await client.post("/chat", json={"message": "Hola"})
        initial_state = mock_graph.ainvoke.call_args[0][0]
        assert initial_state["user_id"] == str(TEST_USER_ID)

    @pytest.mark.asyncio
    async def test_thread_id_combines_user_and_session(self, client, mock_graph):
        session_id = "sess-abc"
        await client.post("/chat", json={"message": "Hola", "session_id": session_id})
        config = mock_graph.ainvoke.call_args[0][1]
        expected_thread = f"{TEST_USER_ID}_{session_id}"
        assert config["configurable"]["thread_id"] == expected_thread


class TestEndSession:
    @pytest.mark.asyncio
    async def test_returns_ok(self, client):
        response = await client.post(
            "/chat/end-session", json={"session_id": "test-session"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["session_id"] == "test-session"

    @pytest.mark.asyncio
    async def test_calls_aget_state_with_correct_thread(self, client, mock_graph):
        session_id = "sess-xyz"
        await client.post("/chat/end-session", json={"session_id": session_id})
        expected_thread = f"{TEST_USER_ID}_{session_id}"
        mock_graph.aget_state.assert_awaited_once_with(
            {"configurable": {"thread_id": expected_thread}}
        )
