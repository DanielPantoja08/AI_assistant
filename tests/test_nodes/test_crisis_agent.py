"""Tests for the crisis_agent node."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage

from logic_graph.models import CrisisAssessment, CrisisLevel


class TestCrisisAgent:
    def _make_state(
        self,
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

    def test_returns_messages_list(self):
        state = self._make_state()
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="Estoy aquí contigo.")
        with patch("logic_graph.nodes.crisis_agent.create_llm_for_node", return_value=mock_llm):
            from logic_graph.nodes.crisis_agent import crisis_agent
            result = crisis_agent(state)
        assert "messages" in result
        assert isinstance(result["messages"], list)
        assert len(result["messages"]) == 1

    def test_returns_generated_response(self):
        state = self._make_state()
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="No estás solo/a.")
        with patch("logic_graph.nodes.crisis_agent.create_llm_for_node", return_value=mock_llm):
            from logic_graph.nodes.crisis_agent import crisis_agent
            result = crisis_agent(state)
        assert result["generated_response"] == "No estás solo/a."

    def test_llm_called_with_system_message(self):
        state = self._make_state()
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="respuesta")
        with patch("logic_graph.nodes.crisis_agent.create_llm_for_node", return_value=mock_llm):
            from logic_graph.nodes.crisis_agent import crisis_agent
            crisis_agent(state)
        call_args = mock_llm.invoke.call_args[0][0]
        from langchain_core.messages import SystemMessage
        assert any(isinstance(m, SystemMessage) for m in call_args)

    def test_assessment_context_included_in_prompt_when_present(self):
        state = self._make_state(
            last_assessment={
                "phq9_score": 22,
                "phq9_severity": "severe",
                "asq_result": "positive_acute",
            }
        )
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="respuesta")
        with patch("logic_graph.nodes.crisis_agent.create_llm_for_node", return_value=mock_llm):
            from logic_graph.nodes.crisis_agent import crisis_agent
            crisis_agent(state)
        call_args = mock_llm.invoke.call_args[0][0]
        system_content = call_args[0].content
        assert "22" in system_content
        assert "severe" in system_content
        assert "positive_acute" in system_content

    def test_works_with_no_assessment(self):
        state = self._make_state(last_assessment=None)
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="respuesta")
        with patch("logic_graph.nodes.crisis_agent.create_llm_for_node", return_value=mock_llm):
            from logic_graph.nodes.crisis_agent import crisis_agent
            result = crisis_agent(state)
        assert "generated_response" in result
