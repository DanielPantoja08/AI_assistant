from __future__ import annotations

from langgraph.store.base import BaseStore

from logic_graph.memory.long_term import load_cumulative_summary, load_profile
from logic_graph.state import GraphState


async def load_user_context(state: GraphState, *, store: BaseStore) -> dict:
    user_id = state.get("user_id", "anonymous")

    profile_data = await load_profile(store, user_id) or {}

    user_summary = await load_cumulative_summary(store, user_id)

    last_assessment = None
    if profile_data and profile_data.get("phq9_score") is not None:
        last_assessment = {
            "phq9_score": profile_data.get("phq9_score"),
            "phq9_severity": profile_data.get("phq9_severity"),
            "asq_result": profile_data.get("asq_result"),
        }

    return {
        "user_profile": profile_data,
        "user_summary": user_summary,
        "last_assessment": last_assessment,
    }
