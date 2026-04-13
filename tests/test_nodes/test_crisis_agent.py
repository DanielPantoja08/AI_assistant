"""Tests for the crisis_agent and crisis_tool_executor nodes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from logic_graph.models import CrisisAssessment, CrisisLevel
from logic_graph.nodes.crisis_agent import _get_crisis_llm_with_tools


@pytest.fixture(autouse=True)
def clear_llm_cache():
    _get_crisis_llm_with_tools.cache_clear()
    yield
    _get_crisis_llm_with_tools.cache_clear()


def _make_state(
    crisis_level: str = "high",
    risk_indicators: list[str] | None = None,
    last_assessment: dict | None = None,
    messages: list | None = None,
) -> dict:
    return {
        "crisis_assessment": CrisisAssessment(
            is_crisis=True,
            crisis_level=CrisisLevel(crisis_level),
            risk_indicators=risk_indicators or ["desesperanza extrema"],
            reasoning="test reasoning",
        ),
        "last_assessment": last_assessment,
        "messages": messages or [HumanMessage(content="no puedo más")],
    }


def _make_ai_response(content="Estoy aquí contigo.", tool_calls=None):
    msg = MagicMock(spec=AIMessage)
    msg.content = content
    msg.tool_calls = tool_calls or []
    return msg


# ---------------------------------------------------------------------------
# crisis_agent
# ---------------------------------------------------------------------------


class TestCrisisAgent:
    def test_final_answer_sets_generated_response(self):
        state = _make_state()
        mock_response = _make_ai_response("No estás solo/a.")
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.return_value = mock_response

        with patch("logic_graph.nodes.crisis_agent.create_llm_for_node", return_value=mock_llm):
            from logic_graph.nodes.crisis_agent import crisis_agent
            result = crisis_agent(state)

        assert result["generated_response"] == "No estás solo/a."
        assert len(result["messages"]) == 1

    def test_tool_call_does_not_set_generated_response(self):
        state = _make_state()
        tool_calls = [{"name": "buscar_recursos_emergencia", "args": {}, "id": "call-1"}]
        mock_response = _make_ai_response(tool_calls=tool_calls)
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.return_value = mock_response

        with patch("logic_graph.nodes.crisis_agent.create_llm_for_node", return_value=mock_llm):
            from logic_graph.nodes.crisis_agent import crisis_agent
            result = crisis_agent(state)

        assert "generated_response" not in result
        assert len(result["messages"]) == 1

    def test_system_message_included_in_invocation(self):
        state = _make_state()
        mock_response = _make_ai_response()
        mock_llm = MagicMock()
        bound = MagicMock()
        bound.invoke.return_value = mock_response
        mock_llm.bind_tools.return_value = bound

        with patch("logic_graph.nodes.crisis_agent.create_llm_for_node", return_value=mock_llm):
            from logic_graph.nodes.crisis_agent import crisis_agent
            crisis_agent(state)

        from langchain_core.messages import SystemMessage
        call_args = bound.invoke.call_args[0][0]
        assert any(isinstance(m, SystemMessage) for m in call_args)

    def test_assessment_context_in_system_prompt(self):
        state = _make_state(
            last_assessment={
                "phq9_score": 22,
                "phq9_severity": "severe",
                "asq_result": "positive_acute",
            }
        )
        mock_response = _make_ai_response()
        mock_llm = MagicMock()
        bound = MagicMock()
        bound.invoke.return_value = mock_response
        mock_llm.bind_tools.return_value = bound

        with patch("logic_graph.nodes.crisis_agent.create_llm_for_node", return_value=mock_llm):
            from logic_graph.nodes.crisis_agent import crisis_agent
            crisis_agent(state)

        from langchain_core.messages import SystemMessage
        call_args = bound.invoke.call_args[0][0]
        system_content = next(m.content for m in call_args if isinstance(m, SystemMessage))
        assert "22" in system_content
        assert "severe" in system_content
        assert "positive_acute" in system_content

    def test_works_with_no_assessment(self):
        state = _make_state(last_assessment=None)
        mock_response = _make_ai_response()
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.return_value = mock_response

        with patch("logic_graph.nodes.crisis_agent.create_llm_for_node", return_value=mock_llm):
            from logic_graph.nodes.crisis_agent import crisis_agent
            result = crisis_agent(state)

        assert "generated_response" in result

    def test_only_emergency_tool_is_bound(self):
        state = _make_state()
        mock_response = _make_ai_response()
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.return_value = mock_response

        with patch("logic_graph.nodes.crisis_agent.create_llm_for_node", return_value=mock_llm):
            from logic_graph.nodes.crisis_agent import crisis_agent
            crisis_agent(state)

        bound_tools = mock_llm.bind_tools.call_args[0][0]
        assert len(bound_tools) == 1
        assert bound_tools[0].name == "buscar_recursos_emergencia"


# ---------------------------------------------------------------------------
# crisis_tool_executor
# ---------------------------------------------------------------------------


class TestCrisisToolExecutor:
    def test_executes_tool_and_returns_tool_messages(self):
        tool_call = {"name": "buscar_recursos_emergencia", "args": {}, "id": "call-1"}
        last_msg = MagicMock()
        last_msg.tool_calls = [tool_call]
        state = {"messages": [last_msg]}

        mock_tool = MagicMock()
        mock_tool.name = "buscar_recursos_emergencia"
        mock_tool.invoke.return_value = "Línea 106: marca 106."

        with patch("logic_graph.nodes.crisis_agent.get_emergency_tools", return_value=[mock_tool]):
            from logic_graph.nodes.crisis_agent import crisis_tool_executor
            result = crisis_tool_executor(state)

        assert "messages" in result
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], ToolMessage)
        assert "106" in result["messages"][0].content

    def test_unknown_tool_returns_error_message(self):
        tool_call = {"name": "herramienta_inexistente", "args": {}, "id": "call-2"}
        last_msg = MagicMock()
        last_msg.tool_calls = [tool_call]
        state = {"messages": [last_msg]}

        mock_tool = MagicMock()
        mock_tool.name = "buscar_recursos_emergencia"

        with patch("logic_graph.nodes.crisis_agent.get_emergency_tools", return_value=[mock_tool]):
            from logic_graph.nodes.crisis_agent import crisis_tool_executor
            result = crisis_tool_executor(state)

        assert "Herramienta no disponible" in result["messages"][0].content

    def test_tool_exception_returns_error_message(self):
        tool_call = {"name": "buscar_recursos_emergencia", "args": {}, "id": "call-3"}
        last_msg = MagicMock()
        last_msg.tool_calls = [tool_call]
        state = {"messages": [last_msg]}

        mock_tool = MagicMock()
        mock_tool.name = "buscar_recursos_emergencia"
        mock_tool.invoke.side_effect = RuntimeError("chroma down")

        with patch("logic_graph.nodes.crisis_agent.get_emergency_tools", return_value=[mock_tool]):
            from logic_graph.nodes.crisis_agent import crisis_tool_executor
            result = crisis_tool_executor(state)

        assert "Error ejecutando" in result["messages"][0].content
