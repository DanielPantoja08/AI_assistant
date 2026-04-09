"""Tests for routing logic (pure functions, no mocks needed)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from logic_graph.models import (
    CrisisAssessment,
    CrisisLevel,
    HallucinationGrade,
)
from logic_graph.routing.edges import (
    route_after_agent,
    route_after_crisis,
    route_after_hallucination,
)


# ---------------------------------------------------------------------------
# route_after_crisis
# ---------------------------------------------------------------------------


class TestRouteAfterCrisis:
    def test_crisis_goes_to_emergency_responder(self):
        state = {
            "crisis_assessment": CrisisAssessment(
                is_crisis=True, crisis_level=CrisisLevel.high, reasoning="test"
            )
        }
        assert route_after_crisis(state) == "emergency_responder"

    def test_no_crisis_goes_to_agent_reasoner(self):
        state = {
            "crisis_assessment": CrisisAssessment(
                is_crisis=False, crisis_level=CrisisLevel.none, reasoning="test"
            )
        }
        assert route_after_crisis(state) == "agent_reasoner"

    def test_imminent_crisis_goes_to_emergency_responder(self):
        state = {
            "crisis_assessment": CrisisAssessment(
                is_crisis=True,
                crisis_level=CrisisLevel.imminent,
                risk_indicators=["ideacion suicida"],
                reasoning="test",
            )
        }
        assert route_after_crisis(state) == "emergency_responder"


# ---------------------------------------------------------------------------
# route_after_agent
# ---------------------------------------------------------------------------


class TestRouteAfterAgent:
    def _make_message_with_tool_calls(self, calls):
        msg = MagicMock()
        msg.tool_calls = calls
        return msg

    def _make_message_without_tool_calls(self):
        msg = MagicMock()
        msg.tool_calls = []
        return msg

    def test_tool_calls_present_goes_to_tool_executor(self):
        msg = self._make_message_with_tool_calls([{"name": "buscar_guias_clinicas", "args": {}, "id": "1"}])
        state = {"messages": [msg]}
        assert route_after_agent(state) == "tool_executor"

    def test_no_tool_calls_goes_to_hallucination_evaluator(self):
        msg = self._make_message_without_tool_calls()
        state = {"messages": [msg]}
        assert route_after_agent(state) == "hallucination_evaluator"

    def test_no_tool_calls_attribute_goes_to_hallucination_evaluator(self):
        msg = MagicMock(spec=[])  # no tool_calls attribute at all
        state = {"messages": [msg]}
        assert route_after_agent(state) == "hallucination_evaluator"


# ---------------------------------------------------------------------------
# route_after_hallucination
# ---------------------------------------------------------------------------


class TestRouteAfterHallucination:
    def test_faithful_goes_to_memory_updater(self):
        state = {
            "hallucination_grade": HallucinationGrade(
                is_faithful=True, reasoning="grounded"
            ),
            "regeneration_count": 0,
        }
        assert route_after_hallucination(state) == "memory_updater"

    def test_unfaithful_regen_count_zero_goes_to_agent_reasoner(self):
        state = {
            "hallucination_grade": HallucinationGrade(
                is_faithful=False, reasoning="hallucinated"
            ),
            "regeneration_count": 0,
        }
        assert route_after_hallucination(state) == "agent_reasoner"

    def test_unfaithful_regen_count_one_goes_to_agent_reasoner(self):
        state = {
            "hallucination_grade": HallucinationGrade(
                is_faithful=False, reasoning="hallucinated"
            ),
            "regeneration_count": 1,
        }
        assert route_after_hallucination(state) == "agent_reasoner"

    def test_unfaithful_regen_count_at_limit_goes_to_memory_updater(self):
        state = {
            "hallucination_grade": HallucinationGrade(
                is_faithful=False, reasoning="hallucinated"
            ),
            "regeneration_count": 2,
        }
        assert route_after_hallucination(state) == "memory_updater"

    def test_unfaithful_regen_count_above_limit_goes_to_memory_updater(self):
        state = {
            "hallucination_grade": HallucinationGrade(
                is_faithful=False, reasoning="hallucinated"
            ),
            "regeneration_count": 5,
        }
        assert route_after_hallucination(state) == "memory_updater"

    def test_missing_regeneration_count_defaults_to_zero(self):
        state = {
            "hallucination_grade": HallucinationGrade(
                is_faithful=False, reasoning="hallucinated"
            ),
        }
        assert route_after_hallucination(state) == "agent_reasoner"
