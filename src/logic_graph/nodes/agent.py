"""Hybrid agent node: ReAct reasoning loop with RAG tool calling."""

from __future__ import annotations

import json
from functools import lru_cache

from langchain_core.messages import SystemMessage, ToolMessage

from logic_graph.llm_factory import create_llm_for_node
from logic_graph.prompts.agent import AGENT_SYSTEM_PROMPT
from logic_graph.state import GraphState
from logic_graph.tools.rag import get_rag_tools


@lru_cache(maxsize=1)
def _get_llm_with_tools():
    """Build and cache the agent LLM with bound RAG tools (one instance per process)."""
    llm = create_llm_for_node("agent")
    tools = get_rag_tools()
    return llm.bind_tools(tools)


def agent_reasoner(state: GraphState) -> dict:
    """Invoke the reasoning agent. Returns tool calls or a final answer."""
    llm_with_tools = _get_llm_with_tools()

    user_profile = state.get("user_profile") or {}
    user_summary = state.get("user_summary") or ""

    system_prompt = AGENT_SYSTEM_PROMPT.format(
        user_profile=user_profile,
        user_summary=user_summary,
    )

    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
    response = llm_with_tools.invoke(messages)

    regeneration_count = state.get("regeneration_count", 0)

    # If this is a regeneration pass (hallucination grade failed), increment counter
    hallucination_grade = state.get("hallucination_grade")
    if hallucination_grade is not None and not hallucination_grade.is_faithful:
        regeneration_count += 1

    result: dict = {
        "messages": [response],
        "regeneration_count": regeneration_count,
    }

    # If no tool calls, this is the final answer
    if not (hasattr(response, "tool_calls") and response.tool_calls):
        result["generated_response"] = response.content

    return result


def tool_executor(state: GraphState) -> dict:
    """Execute tool calls from the last agent message and accumulate retrieved docs."""
    tools = get_rag_tools()
    tool_map = {t.name: t for t in tools}

    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", [])

    tool_messages: list[ToolMessage] = []
    new_docs: list[dict] = []

    for call in tool_calls:
        tool_name = call["name"]
        tool_args = call["args"]
        call_id = call["id"]

        if tool_name not in tool_map:
            content = f"Herramienta desconocida: {tool_name}"
        else:
            try:
                content = tool_map[tool_name].invoke(tool_args)
            except Exception as exc:
                content = f"Error ejecutando {tool_name}: {exc}"

        tool_messages.append(
            ToolMessage(content=content, tool_call_id=call_id, name=tool_name)
        )

        # Parse result text into retrieved_documents format for hallucination check
        if isinstance(content, str) and content != "No se encontraron documentos relevantes.":
            new_docs.append({"content": content, "tool": tool_name})

    existing_docs = state.get("retrieved_documents") or []
    return {
        "messages": tool_messages,
        "retrieved_documents": existing_docs + new_docs,
    }
