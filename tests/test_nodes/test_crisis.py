"""Tests for the crisis_detector node."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from langchain_core.messages import HumanMessage

from logic_graph.models import CrisisAssessment, CrisisLevel


class TestCrisisDetector:
    def _make_state(self, user_input: str = "no puedo más", messages=None):
        return {
            "user_input": user_input,
            "messages": messages or [HumanMessage(content=user_input)],
            "last_assessment": None,
        }

    def test_returns_crisis_assessment(self):
        state = self._make_state()
        mock_result = CrisisAssessment(
            is_crisis=True,
            crisis_level=CrisisLevel.high,
            risk_indicators=["desesperanza"],
            reasoning="test",
        )
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = mock_result
        mock_llm.with_structured_output.return_value = mock_structured

        with patch("logic_graph.nodes.crisis.create_llm_for_node", return_value=mock_llm):
            from logic_graph.nodes.crisis import crisis_detector
            result = crisis_detector(state)

        assert "crisis_assessment" in result
        assert result["crisis_assessment"] is mock_result

    def test_no_crisis_returns_false(self):
        state = self._make_state(user_input="hola, ¿cómo estás?")
        mock_result = CrisisAssessment(
            is_crisis=False,
            crisis_level=CrisisLevel.none,
            reasoning="normal conversation",
        )
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = mock_result
        mock_llm.with_structured_output.return_value = mock_structured

        with patch("logic_graph.nodes.crisis.create_llm_for_node", return_value=mock_llm):
            from logic_graph.nodes.crisis import crisis_detector
            result = crisis_detector(state)

        assert result["crisis_assessment"].is_crisis is False
