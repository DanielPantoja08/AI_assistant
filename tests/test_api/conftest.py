"""Fixtures for API unit tests — no database required."""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from langgraph.store.memory import InMemoryStore

from logic_graph.api import deps
from logic_graph.api.routers import auth as auth_module
from logic_graph.api.routers import chat as chat_module
from logic_graph.auth import current_active_user

TEST_USER_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")


@asynccontextmanager
async def _noop_lifespan(app: FastAPI):
    """No-op lifespan so tests need no running PostgreSQL."""
    yield


def _build_test_app() -> FastAPI:
    test_app = FastAPI(lifespan=_noop_lifespan)
    test_app.include_router(auth_module.router)
    test_app.include_router(chat_module.router)
    return test_app


# --- Shared fixtures ----------------------------------------------------------


@pytest.fixture()
def test_user() -> MagicMock:
    user = MagicMock()
    user.id = TEST_USER_ID
    user.email = "test@test.com"
    user.is_active = True
    return user


@pytest.fixture()
def mock_graph() -> MagicMock:
    graph = MagicMock()
    graph.ainvoke = AsyncMock(
        return_value={"generated_response": "Entiendo cómo te sientes."}
    )
    # Return state with no values so session_finalizer is not triggered in tests.
    graph.aget_state = AsyncMock(return_value=MagicMock(values=None))
    return graph


@pytest.fixture()
def mock_store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture()
def test_app(test_user, mock_graph, mock_store) -> FastAPI:
    """App with all lifecycle deps overridden — authenticated user."""
    app = _build_test_app()
    app.dependency_overrides[current_active_user] = lambda: test_user
    app.dependency_overrides[deps.get_graph] = lambda: mock_graph
    app.dependency_overrides[deps.get_store] = lambda: mock_store
    return app


@pytest.fixture()
def unauth_app(mock_graph, mock_store) -> FastAPI:
    """App with graph/store mocked but auth NOT overridden — for 401 tests."""
    app = _build_test_app()
    app.dependency_overrides[deps.get_graph] = lambda: mock_graph
    app.dependency_overrides[deps.get_store] = lambda: mock_store
    return app


@pytest_asyncio.fixture()
async def client(test_app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture()
async def unauth_client(unauth_app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=unauth_app), base_url="http://test"
    ) as ac:
        yield ac
