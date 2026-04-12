"""Tests for the load_user_context node using InMemoryStore."""

from __future__ import annotations

import pytest
from langgraph.store.memory import InMemoryStore

from logic_graph.nodes.context_loader import load_user_context


class TestLoadUserContext:
    async def test_empty_store_returns_empty_profile_and_no_summary(self, store):
        state = {"user_id": "user1"}
        result = await load_user_context(state, store=store)
        assert result["user_profile"] == {}
        assert result["user_summary"] is None

    async def test_store_with_profile_returns_profile_data(self, store):
        store.put(("user1", "profile"), "clinical_profile", {"total_sessions": 3})
        state = {"user_id": "user1"}
        result = await load_user_context(state, store=store)
        assert result["user_profile"]["total_sessions"] == 3

    async def test_store_with_cumulative_summary_returns_text(self, store):
        store.put(
            ("user1", "sessions"),
            "cumulative_summary",
            {"summary_text": "Talked about anxiety"},
        )
        state = {"user_id": "user1"}
        result = await load_user_context(state, store=store)
        assert result["user_summary"] == "Talked about anxiety"

    async def test_default_user_id_is_anonymous(self, store):
        store.put(
            ("anonymous", "profile"),
            "clinical_profile",
            {"total_sessions": 1},
        )
        state = {}  # No user_id key
        result = await load_user_context(state, store=store)
        assert result["user_profile"]["total_sessions"] == 1

    async def test_user_id_in_state_takes_precedence(self, store):
        store.put(("alice", "profile"), "clinical_profile", {"name": "alice"})
        store.put(("anonymous", "profile"), "clinical_profile", {"name": "anon"})
        state = {"user_id": "alice"}
        result = await load_user_context(state, store=store)
        assert result["user_profile"]["name"] == "alice"

    async def test_profile_and_summary_combined(self, store):
        store.put(("user1", "profile"), "clinical_profile", {"total_sessions": 2})
        store.put(
            ("user1", "sessions"),
            "cumulative_summary",
            {"summary_text": "Resumen acumulativo"},
        )
        state = {"user_id": "user1"}
        result = await load_user_context(state, store=store)
        assert result["user_profile"]["total_sessions"] == 2
        assert result["user_summary"] == "Resumen acumulativo"


@pytest.mark.asyncio
async def test_load_user_context_extracts_assessment_when_present():
    store = InMemoryStore()
    profile = {
        "phq9_score": 18,
        "phq9_severity": "moderately_severe",
        "asq_result": "negative",
        "total_sessions": 1,
        "crisis_count": 0,
        "avg_distress": 3.0,
        "recurring_topics": {},
        "techniques_used": [],
        "last_session_date": "",
    }
    await store.aput(("user1", "profile"), "clinical_profile", profile)
    state = {"user_id": "user1"}
    result = await load_user_context(state, store=store)
    assert result["last_assessment"] == {
        "phq9_score": 18,
        "phq9_severity": "moderately_severe",
        "asq_result": "negative",
    }


@pytest.mark.asyncio
async def test_load_user_context_last_assessment_none_when_no_profile():
    store = InMemoryStore()
    state = {"user_id": "new_user_xyz"}
    result = await load_user_context(state, store=store)
    assert result["last_assessment"] is None


@pytest.mark.asyncio
async def test_load_user_context_last_assessment_none_when_no_phq9():
    store = InMemoryStore()
    profile = {
        "total_sessions": 0,
        "crisis_count": 0,
        "avg_distress": 0.0,
        "recurring_topics": {},
        "techniques_used": [],
        "last_session_date": "",
    }
    await store.aput(("user2", "profile"), "clinical_profile", profile)
    state = {"user_id": "user2"}
    result = await load_user_context(state, store=store)
    assert result["last_assessment"] is None
