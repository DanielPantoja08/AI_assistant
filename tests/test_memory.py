"""Tests for the memory subsystem (short-term and long-term)."""

from __future__ import annotations

import pytest
from langgraph.store.memory import InMemoryStore

from logic_graph.models import EmotionType, SessionMetadata
from logic_graph.memory.short_term import update_session_metadata
from logic_graph.memory.long_term import (
    load_cumulative_summary,
    load_profile,
    save_cumulative_summary,
    save_profile,
    update_clinical_profile,
)


# ---------------------------------------------------------------------------
# update_session_metadata  (short-term)
# ---------------------------------------------------------------------------


class TestUpdateSessionMetadata:
    def test_none_current_returns_new(self, make_session_metadata):
        new = make_session_metadata(
            detected_emotion=EmotionType.anxious,
            distress_level=4,
            topics_mentioned=["sleep"],
            techniques_suggested=["breathing"],
        )
        result = update_session_metadata(None, new)
        assert result is new

    def test_merges_topics_as_set_union(self, make_session_metadata):
        current = make_session_metadata(topics_mentioned=["sleep", "anxiety"])
        new = make_session_metadata(topics_mentioned=["anxiety", "diet"])
        result = update_session_metadata(current, new)
        assert set(result.topics_mentioned) == {"sleep", "anxiety", "diet"}

    def test_merges_techniques_as_set_union(self, make_session_metadata):
        current = make_session_metadata(techniques_suggested=["breathing"])
        new = make_session_metadata(techniques_suggested=["journaling"])
        result = update_session_metadata(current, new)
        assert set(result.techniques_suggested) == {"breathing", "journaling"}

    def test_uses_new_emotion(self, make_session_metadata):
        current = make_session_metadata(detected_emotion=EmotionType.calm)
        new = make_session_metadata(detected_emotion=EmotionType.anxious)
        result = update_session_metadata(current, new)
        assert result.detected_emotion == EmotionType.anxious

    def test_uses_new_distress_level(self, make_session_metadata):
        current = make_session_metadata(distress_level=2)
        new = make_session_metadata(distress_level=5)
        result = update_session_metadata(current, new)
        assert result.distress_level == 5

    def test_crisis_activated_sticky_true(self, make_session_metadata):
        """Once crisis is activated in the session, it stays True."""
        current = make_session_metadata(crisis_activated=True)
        new = make_session_metadata(crisis_activated=False)
        result = update_session_metadata(current, new)
        assert result.crisis_activated is True

    def test_crisis_activated_becomes_true(self, make_session_metadata):
        current = make_session_metadata(crisis_activated=False)
        new = make_session_metadata(crisis_activated=True)
        result = update_session_metadata(current, new)
        assert result.crisis_activated is True

    def test_crisis_activated_stays_false(self, make_session_metadata):
        current = make_session_metadata(crisis_activated=False)
        new = make_session_metadata(crisis_activated=False)
        result = update_session_metadata(current, new)
        assert result.crisis_activated is False


# ---------------------------------------------------------------------------
# load_profile / save_profile  (long-term)
# ---------------------------------------------------------------------------


class TestLoadSaveProfile:
    async def test_load_empty_store_returns_none(self, store):
        assert await load_profile(store, "user1") is None

    async def test_save_then_load_returns_profile(self, store):
        profile_data = {"total_sessions": 3, "avg_distress": 2.5}
        await save_profile(store, "user1", profile_data)
        loaded = await load_profile(store, "user1")
        assert loaded == profile_data

    async def test_load_isolates_users(self, store):
        await save_profile(store, "alice", {"name": "alice"})
        assert await load_profile(store, "bob") is None

    async def test_save_overwrites_existing(self, store):
        await save_profile(store, "user1", {"total_sessions": 1})
        await save_profile(store, "user1", {"total_sessions": 2})
        loaded = await load_profile(store, "user1")
        assert loaded["total_sessions"] == 2


# ---------------------------------------------------------------------------
# load_cumulative_summary / save_cumulative_summary  (long-term)
# ---------------------------------------------------------------------------


class TestCumulativeSummary:
    async def test_load_empty_store_returns_none(self, store):
        result = await load_cumulative_summary(store, "user1")
        assert result is None

    async def test_save_then_load_returns_text(self, store):
        await save_cumulative_summary(store, "user1", "El usuario expresó ansiedad.")
        result = await load_cumulative_summary(store, "user1")
        assert result == "El usuario expresó ansiedad."

    async def test_update_overwrites_previous(self, store):
        await save_cumulative_summary(store, "user1", "Resumen inicial.")
        await save_cumulative_summary(store, "user1", "Resumen actualizado con nueva sesión.")
        result = await load_cumulative_summary(store, "user1")
        assert result == "Resumen actualizado con nueva sesión."

    async def test_summaries_isolated_per_user(self, store):
        await save_cumulative_summary(store, "alice", "Resumen de alice.")
        result = await load_cumulative_summary(store, "bob")
        assert result is None


# ---------------------------------------------------------------------------
# update_clinical_profile  (long-term)
# ---------------------------------------------------------------------------


class TestUpdateClinicalProfile:
    async def test_first_update_from_blank(self, store, make_session_metadata):
        metadata = make_session_metadata(
            distress_level=3,
            topics_mentioned=["anxiety"],
            techniques_suggested=["breathing"],
            crisis_activated=False,
        )
        await update_clinical_profile(store, "user1", metadata)

        profile = await load_profile(store, "user1")
        assert profile is not None
        assert profile["total_sessions"] == 1
        assert profile["avg_distress"] == 3.0
        assert profile["recurring_topics"]["anxiety"] == 1
        assert "breathing" in profile["techniques_used"]
        assert profile["crisis_count"] == 0

    async def test_second_update_weighted_average(self, store, make_session_metadata):
        meta1 = make_session_metadata(
            distress_level=4,
            topics_mentioned=["sleep"],
            techniques_suggested=["journaling"],
            crisis_activated=False,
        )
        await update_clinical_profile(store, "user1", meta1)

        meta2 = make_session_metadata(
            distress_level=2,
            topics_mentioned=["sleep", "diet"],
            techniques_suggested=["breathing"],
            crisis_activated=False,
        )
        await update_clinical_profile(store, "user1", meta2)

        profile = await load_profile(store, "user1")
        assert profile["total_sessions"] == 2
        assert profile["avg_distress"] == 3.0
        assert profile["recurring_topics"]["sleep"] == 2
        assert profile["recurring_topics"]["diet"] == 1
        assert set(profile["techniques_used"]) == {"journaling", "breathing"}

    async def test_crisis_count_increments(self, store, make_session_metadata):
        meta = make_session_metadata(crisis_activated=True)
        await update_clinical_profile(store, "user1", meta)
        profile = await load_profile(store, "user1")
        assert profile["crisis_count"] == 1

    async def test_crisis_count_stays_same_when_no_crisis(
        self, store, make_session_metadata
    ):
        meta1 = make_session_metadata(crisis_activated=True)
        await update_clinical_profile(store, "user1", meta1)

        meta2 = make_session_metadata(crisis_activated=False)
        await update_clinical_profile(store, "user1", meta2)

        profile = await load_profile(store, "user1")
        assert profile["crisis_count"] == 1

    async def test_multiple_crisis_sessions(self, store, make_session_metadata):
        for _ in range(3):
            meta = make_session_metadata(crisis_activated=True)
            await update_clinical_profile(store, "user1", meta)

        profile = await load_profile(store, "user1")
        assert profile["crisis_count"] == 3
        assert profile["total_sessions"] == 3

    async def test_last_session_date_is_set(self, store, make_session_metadata):
        meta = make_session_metadata()
        await update_clinical_profile(store, "user1", meta)
        profile = await load_profile(store, "user1")
        assert profile["last_session_date"]
        assert len(profile["last_session_date"]) == 10
