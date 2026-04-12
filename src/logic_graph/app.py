from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.store.memory import InMemoryStore

from logic_graph.nodes import (
    agent_reasoner,
    crisis_agent,
    crisis_detector,
    emergency_responder,
    hallucination_evaluator,
    load_user_context,
    memory_updater,
    tool_executor,
)
from logic_graph.routing.edges import (
    route_after_agent,
    route_after_crisis,
    route_after_hallucination,
)
from logic_graph.state import GraphState


def build_graph(
    checkpointer=None,
    store=None,
) -> StateGraph:
    builder = StateGraph(GraphState)

    # --- Nodes ---
    builder.add_node("load_user_context", load_user_context)
    builder.add_node("crisis_detector", crisis_detector)
    builder.add_node("crisis_agent", crisis_agent)
    builder.add_node("emergency_responder", emergency_responder)
    builder.add_node("agent_reasoner", agent_reasoner)
    builder.add_node("tool_executor", tool_executor)
    builder.add_node("hallucination_evaluator", hallucination_evaluator)
    builder.add_node("memory_updater", memory_updater)

    # --- Edges ---

    # Entry
    builder.add_edge(START, "load_user_context")
    builder.add_edge("load_user_context", "crisis_detector")

    # Crisis gate
    builder.add_conditional_edges(
        "crisis_detector",
        route_after_crisis,
        ["crisis_agent", "agent_reasoner"],
    )

    # ReAct loop: agent ↔ tool_executor
    builder.add_conditional_edges(
        "agent_reasoner",
        route_after_agent,
        ["tool_executor", "hallucination_evaluator"],
    )
    builder.add_edge("tool_executor", "agent_reasoner")

    # Hallucination check + optional regen loop
    builder.add_conditional_edges(
        "hallucination_evaluator",
        route_after_hallucination,
        ["memory_updater", "agent_reasoner"],
    )

    # Terminal paths
    builder.add_edge("crisis_agent", "emergency_responder")
    builder.add_edge("emergency_responder", "memory_updater")
    builder.add_edge("memory_updater", END)

    # Compile
    if checkpointer is None:
        checkpointer = MemorySaver()
    if store is None:
        store = InMemoryStore()

    return builder.compile(checkpointer=checkpointer, store=store)


def main() -> None:
    """CLI entry point — runs the graph interactively with in-memory backends."""
    import sys

    from langchain_core.messages import HumanMessage

    graph = build_graph()
    user_id = "cli_user"
    thread_id = f"{user_id}_session_1"
    config = {"configurable": {"thread_id": thread_id}}

    print("Logic Graph CLI — escribe 'salir' para terminar.\n")
    while True:
        try:
            user_input = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)

        if user_input.lower() in {"salir", "exit", "quit"}:
            sys.exit(0)

        if not user_input:
            continue

        result = graph.invoke(
            {"user_input": user_input, "messages": [HumanMessage(content=user_input)], "user_id": user_id},
            config,
        )
        response = result.get("generated_response", "")
        print(f"Asistente: {response}\n")
