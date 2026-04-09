from __future__ import annotations

import operator
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage

from logic_graph.models import (
    CrisisAssessment,
    HallucinationGrade,
    SessionMetadata,
)


class GraphState(TypedDict):
    # Conversation
    messages: Annotated[list[BaseMessage], operator.add]
    user_input: str

    # Crisis detection
    crisis_assessment: Optional[CrisisAssessment]

    # RAG processing (populated by tool_executor)
    retrieved_documents: list[dict]

    # Response generation
    generated_response: str
    hallucination_grade: Optional[HallucinationGrade]
    regeneration_count: int  # Max 2 regenerations

    # Session memory (short term)
    session_metadata: Optional[SessionMetadata]

    # User context (long term, loaded from Store)
    user_id: str
    user_profile: Optional[dict]
    user_summary: Optional[str]
