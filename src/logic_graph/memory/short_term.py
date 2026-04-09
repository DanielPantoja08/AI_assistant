from __future__ import annotations

from logic_graph.models import SessionMetadata


def update_session_metadata(
    current: SessionMetadata | None, new: SessionMetadata
) -> SessionMetadata:
    if current is None:
        return new

    merged_topics = list(set(current.topics_mentioned) | set(new.topics_mentioned))
    merged_techniques = list(
        set(current.techniques_suggested) | set(new.techniques_suggested)
    )

    return SessionMetadata(
        detected_emotion=new.detected_emotion,
        distress_level=new.distress_level,
        topics_mentioned=merged_topics,
        techniques_suggested=merged_techniques,
        crisis_activated=current.crisis_activated or new.crisis_activated,
    )
