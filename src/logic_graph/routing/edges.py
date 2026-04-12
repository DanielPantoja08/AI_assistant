from __future__ import annotations

from typing import Literal

from logic_graph.state import GraphState


def route_after_crisis(
    state: GraphState,
) -> Literal["crisis_agent", "agent_reasoner"]:
    if state["crisis_assessment"].is_crisis:
        return "crisis_agent"
    return "agent_reasoner"


def route_after_agent(
    state: GraphState,
) -> Literal["tool_executor", "hallucination_evaluator"]:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tool_executor"
    return "hallucination_evaluator"


def route_after_hallucination(
    state: GraphState,
) -> Literal["memory_updater", "agent_reasoner"]:
    if state["hallucination_grade"].is_faithful:
        return "memory_updater"
    if state.get("regeneration_count", 0) < 2:
        return "agent_reasoner"
    return "memory_updater"
