from __future__ import annotations

from datetime import datetime

from langgraph.store.base import BaseStore

from logic_graph.models import ClinicalProfile, SessionMetadata


async def load_profile(store: BaseStore, user_id: str) -> dict | None:
    results = await store.asearch((user_id, "profile"))
    for item in results:
        if item.key == "clinical_profile":
            return item.value
    return None


async def save_profile(store: BaseStore, user_id: str, profile: dict) -> None:
    await store.aput((user_id, "profile"), "clinical_profile", profile)


async def load_cumulative_summary(store: BaseStore, user_id: str) -> str | None:
    results = await store.asearch((user_id, "sessions"))
    for item in results:
        if item.key == "cumulative_summary":
            return item.value.get("summary_text")
    return None


async def save_cumulative_summary(store: BaseStore, user_id: str, summary_text: str) -> None:
    await store.aput((user_id, "sessions"), "cumulative_summary", {"summary_text": summary_text})


async def update_clinical_profile(
    store: BaseStore, user_id: str, session_metadata: SessionMetadata
) -> None:
    existing = await load_profile(store, user_id)

    if existing:
        profile = ClinicalProfile(**existing)
    else:
        profile = ClinicalProfile(
            recurring_topics={},
            total_sessions=0,
            crisis_count=0,
            avg_distress=0.0,
            techniques_used=[],
            last_session_date="",
        )

    old_total = profile.total_sessions
    new_total = old_total + 1

    if old_total > 0:
        new_avg = (profile.avg_distress * old_total + session_metadata.distress_level) / new_total
    else:
        new_avg = float(session_metadata.distress_level)

    updated_topics = dict(profile.recurring_topics)
    for topic in session_metadata.topics_mentioned:
        updated_topics[topic] = updated_topics.get(topic, 0) + 1

    merged_techniques = list(
        set(profile.techniques_used) | set(session_metadata.techniques_suggested)
    )

    crisis_count = profile.crisis_count
    if session_metadata.crisis_activated:
        crisis_count += 1

    updated_profile = ClinicalProfile(
        recurring_topics=updated_topics,
        total_sessions=new_total,
        crisis_count=crisis_count,
        avg_distress=round(new_avg, 2),
        techniques_used=merged_techniques,
        last_session_date=datetime.now().strftime("%Y-%m-%d"),
    )

    await save_profile(store, user_id, updated_profile.model_dump())
