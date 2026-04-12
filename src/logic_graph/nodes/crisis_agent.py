"""Crisis agent node: empathic de-escalation before emergency resources."""

from __future__ import annotations

from langchain_core.messages import SystemMessage

from logic_graph.llm_factory import create_llm_for_node
from logic_graph.prompts.crisis_agent import CRISIS_AGENT_SYSTEM_PROMPT
from logic_graph.state import GraphState


def _format_assessment_context(last_assessment: dict | None) -> str:
    if not last_assessment:
        return "Sin evaluación disponible para hoy."
    score = last_assessment.get("phq9_score")
    severity = last_assessment.get("phq9_severity", "desconocida")
    asq = last_assessment.get("asq_result", "desconocido")
    return (
        f"PHQ-9: {score} puntos — severidad: {severity}\n"
        f"ASQ: {asq}"
    )


def crisis_agent(state: GraphState) -> dict:
    """Generate an empathic de-escalation message before showing emergency lines."""
    llm = create_llm_for_node("crisis_agent")

    crisis_assessment = state.get("crisis_assessment")
    last_assessment = state.get("last_assessment")

    crisis_level = crisis_assessment.crisis_level.value if crisis_assessment else "desconocido"
    risk_indicators = crisis_assessment.risk_indicators if crisis_assessment else []

    system_prompt = CRISIS_AGENT_SYSTEM_PROMPT.format(
        assessment_context=_format_assessment_context(last_assessment),
        crisis_level=crisis_level,
        risk_indicators=", ".join(risk_indicators) if risk_indicators else "no especificados",
    )

    recent_messages = list(state.get("messages", []))[-5:]
    messages = [SystemMessage(content=system_prompt)] + recent_messages

    response = llm.invoke(messages)

    return {
        "messages": [response],
        "generated_response": response.content,
    }
