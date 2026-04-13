"""Integration tests for the hybrid agent psychoeducation chatbot graph."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from logic_graph.app import build_graph
from logic_graph.memory.long_term import load_profile
from logic_graph.models import (
    CrisisAssessment,
    CrisisLevel,
    EmotionType,
    HallucinationGrade,
    SessionMetadata,
)
from logic_graph.nodes.crisis_agent import _get_crisis_llm_with_tools

# Patch create_llm_for_node at the module level where it's imported.
# The agent node and other nodes use local bindings via `from X import Y`.
_PATCH_TARGETS = [
    "logic_graph.nodes.agent.create_llm_for_node",
    "logic_graph.nodes.crisis.create_llm_for_node",
    "logic_graph.nodes.crisis_agent.create_llm_for_node",
    "logic_graph.nodes.hallucination.create_llm_for_node",
    "logic_graph.nodes.memory.create_llm_for_node",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_llm(structured_return=None, plain_content="Respuesta de prueba"):
    """Create a mock LLM supporting both .invoke() and .with_structured_output().invoke()."""
    mock_llm = MagicMock()

    # Use a real AIMessage so LangGraph's checkpointer can serialize it
    plain_response = AIMessage(content=plain_content)
    mock_llm.invoke.return_value = plain_response

    if structured_return is not None:
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = structured_return
        mock_llm.with_structured_output.return_value = mock_structured

    # bind_tools returns a mock that produces a real AIMessage (no tool calls → final answer)
    bound_llm = MagicMock()
    bound_llm.invoke.return_value = AIMessage(content=plain_content)
    mock_llm.bind_tools.return_value = bound_llm

    return mock_llm


def _build_llm_factory(overrides: dict[str, MagicMock]):
    """Return a side_effect for create_llm_for_node dispatching by node name."""

    def factory(node_name: str, **kwargs):
        if node_name in overrides:
            return overrides[node_name]
        return _make_mock_llm(plain_content="fallback mock")

    return factory


def _agent_mocks() -> dict[str, MagicMock]:
    """Mock LLMs for the happy-path agent flow (no tool calls)."""
    return {
        "agent": _make_mock_llm(plain_content="Respuesta de prueba"),
        "crisis_detector": _make_mock_llm(
            structured_return=CrisisAssessment(
                is_crisis=False,
                crisis_level=CrisisLevel.none,
                risk_indicators=[],
                reasoning="test",
            ),
        ),
        "hallucination_evaluator": _make_mock_llm(
            structured_return=HallucinationGrade(
                is_faithful=True,
                unfaithful_claims=[],
                reasoning="test",
            ),
        ),
        "memory_summarizer": _make_mock_llm(
            structured_return=SessionMetadata(
                detected_emotion=EmotionType.neutral,
                distress_level=2,
                topics_mentioned=["depresion"],
                techniques_suggested=[],
                crisis_activated=False,
            ),
        ),
    }


def _crisis_mocks() -> dict[str, MagicMock]:
    """Mock LLMs for the crisis path."""
    return {
        "crisis_detector": _make_mock_llm(
            structured_return=CrisisAssessment(
                is_crisis=True,
                crisis_level=CrisisLevel.high,
                risk_indicators=["ideacion suicida"],
                reasoning="test",
            ),
        ),
        "crisis_agent": _make_mock_llm(plain_content="Entiendo que estás pasando por algo muy difícil."),
        "memory_summarizer": _make_mock_llm(
            structured_return=SessionMetadata(
                detected_emotion=EmotionType.neutral,
                distress_level=2,
                topics_mentioned=["depresion"],
                techniques_suggested=[],
                crisis_activated=True,
            ),
        ),
    }


def _apply_patches(factory_fn):
    """Apply create_llm_for_node patches to all node modules."""
    patches = []
    for target in _PATCH_TARGETS:
        p = patch(target, side_effect=factory_fn)
        p.start()
        patches.append(p)
    return patches


def _stop_patches(patches):
    for p in patches:
        p.stop()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGraphCompilation:
    def test_graph_compiles(self):
        graph = build_graph(
            checkpointer=MemorySaver(),
            store=InMemoryStore(),
        )
        assert graph is not None


class TestAgentPath:
    async def test_end_to_end_no_tool_calls(self):
        factory_fn = _build_llm_factory(_agent_mocks())
        patches = _apply_patches(factory_fn)
        try:
            store = InMemoryStore()
            graph = build_graph(checkpointer=MemorySaver(), store=store)

            initial_state = {
                "user_input": "Que es la depresion?",
                "user_id": "test_user",
                "messages": [],
            }
            config = {"configurable": {"thread_id": "t1"}}

            result = await graph.ainvoke(initial_state, config=config)

            assert result is not None
            assert "generated_response" in result
            assert len(result["generated_response"]) > 0
            assert result["session_metadata"] is not None
        finally:
            _stop_patches(patches)


class TestCrisisPath:
    async def test_crisis_triggers_crisis_agent(self):
        _get_crisis_llm_with_tools.cache_clear()
        factory_fn = _build_llm_factory(_crisis_mocks())
        patches = _apply_patches(factory_fn)
        try:
            store = InMemoryStore()
            graph = build_graph(checkpointer=MemorySaver(), store=store)

            initial_state = {
                "user_input": "No quiero seguir viviendo",
                "user_id": "test_user",
                "messages": [],
            }
            config = {"configurable": {"thread_id": "t_crisis"}}

            result = await graph.ainvoke(initial_state, config=config)

            assert result is not None
            assert "generated_response" in result
            assert len(result["generated_response"]) > 0
        finally:
            _get_crisis_llm_with_tools.cache_clear()
            _stop_patches(patches)


class TestStorePersistenceAcrossThreads:
    async def test_store_persists_across_threads(self):
        factory_fn = _build_llm_factory(_agent_mocks())
        patches = _apply_patches(factory_fn)
        try:
            store = InMemoryStore()
            checkpointer = MemorySaver()
            graph = build_graph(checkpointer=checkpointer, store=store)

            base_state = {
                "user_input": "Que es la ansiedad?",
                "user_id": "test_user",
                "messages": [],
            }

            # Thread 1: runs with empty store
            result_1 = await graph.ainvoke(
                base_state,
                config={"configurable": {"thread_id": "thread_1"}},
            )
            assert result_1["user_profile"] == {}

            # Simulate what session_finalizer would do
            from logic_graph.memory.long_term import update_clinical_profile
            await update_clinical_profile(store, "test_user", result_1["session_metadata"])

            profile_after_t1 = await load_profile(store, "test_user")
            assert profile_after_t1 is not None
            assert profile_after_t1["total_sessions"] == 1

            # Thread 2: same store, different thread
            result_2 = await graph.ainvoke(
                base_state,
                config={"configurable": {"thread_id": "thread_2"}},
            )
            assert result_2["user_profile"] is not None
            assert result_2["user_profile"]["total_sessions"] == 1

            await update_clinical_profile(store, "test_user", result_2["session_metadata"])

            profile_after_t2 = await load_profile(store, "test_user")
            assert profile_after_t2 is not None
            assert profile_after_t2["total_sessions"] == 2
        finally:
            _stop_patches(patches)
