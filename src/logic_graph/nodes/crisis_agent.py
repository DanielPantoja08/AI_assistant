"""Crisis agent node: empathic ReAct agent with emergency RAG access."""

from __future__ import annotations

from functools import lru_cache

from langchain_core.messages import SystemMessage, ToolMessage

from logic_graph.llm_factory import create_llm_for_node
from logic_graph.prompts.crisis_agent import CRISIS_AGENT_SYSTEM_PROMPT
from logic_graph.state import GraphState
from logic_graph.tools.rag import get_emergency_tools


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


@lru_cache(maxsize=1)
def _get_crisis_llm_with_tools():
    """Build and cache the crisis agent LLM with emergency tool bound."""
    llm = create_llm_for_node("crisis_agent")
    tools = get_emergency_tools()
    return llm.bind_tools(tools)


def crisis_agent(state: GraphState) -> dict:
    """Empathic crisis agent: uses emergency RAG to synthesize contextual help."""
    llm_with_tools = _get_crisis_llm_with_tools()

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

    response = llm_with_tools.invoke(messages)

    result: dict = {"messages": [response]}

    if not (hasattr(response, "tool_calls") and response.tool_calls):
        result["generated_response"] = response.content

    return result


def crisis_tool_executor(state: GraphState) -> dict:
    """Execute emergency tool calls from the crisis agent."""
    tools = get_emergency_tools()
    tool_map = {t.name: t for t in tools}

    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", [])

    tool_messages: list[ToolMessage] = []

    for call in tool_calls:
        tool_name = call["name"]
        tool_args = call["args"]
        call_id = call["id"]

        if tool_name not in tool_map:
            content = f"Herramienta no disponible: {tool_name}"
        else:
            try:
                content = tool_map[tool_name].invoke(tool_args)
            except Exception as exc:
                content = f"Error ejecutando {tool_name}: {exc}"

        tool_messages.append(
            ToolMessage(content=content, tool_call_id=call_id, name=tool_name)
        )

    return {"messages": tool_messages}
