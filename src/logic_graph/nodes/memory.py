from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.store.base import BaseStore

from logic_graph.llm_factory import create_llm_for_node
from logic_graph.memory import long_term
from logic_graph.memory.short_term import update_session_metadata
from logic_graph.models import SessionMetadata
from logic_graph.prompts import (
    CUMULATIVE_SUMMARY_SYSTEM_PROMPT,
    METADATA_EXTRACTION_SYSTEM_PROMPT,
)
from logic_graph.state import GraphState


def _format_conversation(state: GraphState) -> str:
    parts = []
    for msg in state["messages"]:
        role = "Usuario" if isinstance(msg, HumanMessage) else "Asistente"
        parts.append(f"{role}: {msg.content}")
    return "\n".join(parts)


def memory_updater(state: GraphState) -> dict:
    llm = create_llm_for_node("memory_summarizer")
    structured_llm = llm.with_structured_output(SessionMetadata, method="json_mode")

    conversation_text = _format_conversation(state)
    result = structured_llm.invoke([
        SystemMessage(content=METADATA_EXTRACTION_SYSTEM_PROMPT),
        HumanMessage(content=conversation_text),
    ])

    merged = update_session_metadata(state.get("session_metadata"), result)
    # The agent already appended its AIMessage to messages via the reducer.
    # Only return the updated session metadata here.
    return {"session_metadata": merged}


async def session_finalizer(state: GraphState, *, store: BaseStore) -> None:
    llm = create_llm_for_node("memory_summarizer")
    user_id = state.get("user_id", "anonymous")

    existing_summary = await long_term.load_cumulative_summary(store, user_id) or ""
    conversation_text = _format_conversation(state)

    user_message = f"""## Resumen acumulativo actual
{existing_summary if existing_summary else "(Sin resumen previo — esta es la primera sesión)"}

## Conversación de la sesión actual
{conversation_text}"""

    response = llm.invoke([
        SystemMessage(content=CUMULATIVE_SUMMARY_SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ])

    await long_term.save_cumulative_summary(store, user_id, response.content)

    if state.get("session_metadata"):
        await long_term.update_clinical_profile(store, user_id, state["session_metadata"])
