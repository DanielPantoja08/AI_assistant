"""Shared fixtures for the logic_graph test suite."""

from __future__ import annotations

import os

# Set required env vars before any logic_graph module is imported.
# These are safe placeholder values used only during testing.
os.environ.setdefault(
    "LG_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test"
)
os.environ.setdefault("LG_JWT_SECRET", "test-secret-key-for-pytest-only")

import pytest
from langgraph.store.memory import InMemoryStore

from logic_graph.models import (
    CrisisAssessment,
    CrisisLevel,
    EmotionType,
    HallucinationGrade,
    SessionMetadata,
)


@pytest.fixture()
def store() -> InMemoryStore:
    """Return a fresh in-memory store for each test."""
    return InMemoryStore()


# ---- Reusable model factories ------------------------------------------------


@pytest.fixture()
def make_crisis():
    """Factory for CrisisAssessment instances."""

    def _make(
        is_crisis: bool = False,
        crisis_level: CrisisLevel = CrisisLevel.none,
        risk_indicators: list[str] | None = None,
        reasoning: str = "test",
    ) -> CrisisAssessment:
        return CrisisAssessment(
            is_crisis=is_crisis,
            crisis_level=crisis_level,
            risk_indicators=risk_indicators or [],
            reasoning=reasoning,
        )

    return _make


@pytest.fixture()
def make_hallucination():
    """Factory for HallucinationGrade instances."""

    def _make(
        is_faithful: bool = True,
        unfaithful_claims: list[str] | None = None,
        reasoning: str = "test",
    ) -> HallucinationGrade:
        return HallucinationGrade(
            is_faithful=is_faithful,
            unfaithful_claims=unfaithful_claims or [],
            reasoning=reasoning,
        )

    return _make


@pytest.fixture()
def make_session_metadata():
    """Factory for SessionMetadata instances."""

    def _make(
        detected_emotion: EmotionType = EmotionType.neutral,
        distress_level: int = 3,
        topics_mentioned: list[str] | None = None,
        techniques_suggested: list[str] | None = None,
        crisis_activated: bool = False,
    ) -> SessionMetadata:
        return SessionMetadata(
            detected_emotion=detected_emotion,
            distress_level=distress_level,
            topics_mentioned=topics_mentioned or [],
            techniques_suggested=techniques_suggested or [],
            crisis_activated=crisis_activated,
        )

    return _make
