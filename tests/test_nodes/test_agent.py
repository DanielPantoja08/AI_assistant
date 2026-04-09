"""Tests for agent_reasoner and tool_executor nodes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from logic_graph.models import HallucinationGrade


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_agent_response(content="Respuesta de prueba", tool_calls=None):
    """Build a mock AIMessage with optional tool_calls."""
    msg = MagicMock(spec=AIMessage)
    msg.content = content
    msg.tool_calls = tool_calls or []
    return msg


def _base_state(messages=None, **extra):
    return {
        "messages": messages or [HumanMessage(content="Hola")],
        "user_profile": {},
        "user_summary": "",
        "retrieved_documents": [],
        **extra,
    }


# ---------------------------------------------------------------------------
# agent_reasoner
# ---------------------------------------------------------------------------


class TestAgentReasoner:
    def test_final_answer_sets_generated_response(self):
        mock_response = _make_agent_response(content="Una respuesta empática.")

        mock_bound_llm = MagicMock()
        mock_bound_llm.invoke.return_value = mock_response

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_bound_llm

        with patch("logic_graph.nodes.agent.create_llm_for_node", return_value=mock_llm):
            from logic_graph.nodes.agent import agent_reasoner
            result = agent_reasoner(_base_state())

        assert result["generated_response"] == "Una respuesta empática."
        assert result["messages"] == [mock_response]
        assert result["regeneration_count"] == 0

    def test_tool_calls_do_not_set_generated_response(self):
        mock_response = _make_agent_response(
            tool_calls=[{"name": "buscar_guias_clinicas", "args": {"query": "depresion"}, "id": "c1"}]
        )

        mock_bound_llm = MagicMock()
        mock_bound_llm.invoke.return_value = mock_response

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_bound_llm

        with patch("logic_graph.nodes.agent.create_llm_for_node", return_value=mock_llm):
            from logic_graph.nodes.agent import agent_reasoner
            result = agent_reasoner(_base_state())

        assert "generated_response" not in result
        assert result["messages"] == [mock_response]

    def test_regeneration_increments_on_unfaithful_grade(self):
        mock_response = _make_agent_response(content="Regenerada.")
        mock_bound_llm = MagicMock()
        mock_bound_llm.invoke.return_value = mock_response
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_bound_llm

        state = _base_state(
            regeneration_count=1,
            hallucination_grade=HallucinationGrade(
                is_faithful=False,
                unfaithful_claims=["afirmacion falsa"],
                reasoning="not grounded",
            ),
        )

        with patch("logic_graph.nodes.agent.create_llm_for_node", return_value=mock_llm):
            from logic_graph.nodes.agent import agent_reasoner
            result = agent_reasoner(state)

        assert result["regeneration_count"] == 2


# ---------------------------------------------------------------------------
# tool_executor
# ---------------------------------------------------------------------------


class TestToolExecutor:
    def test_executes_tool_and_returns_tool_messages(self):
        tool_call = {
            "name": "buscar_guias_clinicas",
            "args": {"query": "depresion"},
            "id": "call_1",
        }
        last_msg = MagicMock()
        last_msg.tool_calls = [tool_call]

        mock_tool = MagicMock()
        mock_tool.name = "buscar_guias_clinicas"
        mock_tool.invoke.return_value = "[1] Documento clínico sobre depresión."

        with patch("logic_graph.nodes.agent.get_rag_tools", return_value=[mock_tool]):
            from logic_graph.nodes.agent import tool_executor
            state = _base_state(messages=[last_msg])
            result = tool_executor(state)

        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], ToolMessage)
        assert result["messages"][0].tool_call_id == "call_1"
        assert len(result["retrieved_documents"]) == 1
        assert result["retrieved_documents"][0]["tool"] == "buscar_guias_clinicas"

    def test_accumulates_existing_retrieved_documents(self):
        tool_call = {
            "name": "buscar_tecnicas_tcc",
            "args": {"query": "respiracion"},
            "id": "call_2",
        }
        last_msg = MagicMock()
        last_msg.tool_calls = [tool_call]

        mock_tool = MagicMock()
        mock_tool.name = "buscar_tecnicas_tcc"
        mock_tool.invoke.return_value = "[1] Ejercicio de respiración diafragmática."

        with patch("logic_graph.nodes.agent.get_rag_tools", return_value=[mock_tool]):
            from logic_graph.nodes.agent import tool_executor
            existing = [{"content": "doc previo", "tool": "buscar_guias_clinicas"}]
            state = _base_state(messages=[last_msg], retrieved_documents=existing)
            result = tool_executor(state)

        assert len(result["retrieved_documents"]) == 2

    def test_unknown_tool_returns_error_message(self):
        tool_call = {"name": "herramienta_inexistente", "args": {}, "id": "call_3"}
        last_msg = MagicMock()
        last_msg.tool_calls = [tool_call]

        with patch("logic_graph.nodes.agent.get_rag_tools", return_value=[]):
            from logic_graph.nodes.agent import tool_executor
            state = _base_state(messages=[last_msg])
            result = tool_executor(state)

        assert "Herramienta desconocida" in result["messages"][0].content
