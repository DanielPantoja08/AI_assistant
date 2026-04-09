from __future__ import annotations

from langgraph.store.base import BaseStore

from logic_graph.memory.long_term import load_cumulative_summary
from logic_graph.state import GraphState


async def load_user_context(state: GraphState, *, store: BaseStore) -> dict:
    user_id = state.get("user_id", "anonymous")

    profile_results = await store.asearch((user_id, "profile"))
    profile_data = profile_results[0].value if profile_results else {}

    user_summary = await load_cumulative_summary(store, user_id)

    return {"user_profile": profile_data, "user_summary": user_summary}
