from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class CrisisLevel(StrEnum):
    none = "none"
    low = "low"
    medium = "medium"
    high = "high"
    imminent = "imminent"


class EmotionType(StrEnum):
    sad = "sad"
    anxious = "anxious"
    angry = "angry"
    hopeless = "hopeless"
    neutral = "neutral"
    calm = "calm"
    other = "other"


# ---------------------------------------------------------------------------
# Structured output models
# ---------------------------------------------------------------------------


class CrisisAssessment(BaseModel):
    is_crisis: bool
    crisis_level: CrisisLevel
    risk_indicators: list[str] = Field(default_factory=list)
    reasoning: str

    @field_validator("is_crisis", mode="before")
    @classmethod
    def coerce_bool(cls, v: Any) -> bool:
        if isinstance(v, str):
            return v.lower() == "true"
        return bool(v)


class HallucinationGrade(BaseModel):
    is_faithful: bool
    unfaithful_claims: list[str] = Field(default_factory=list)
    reasoning: str

    @field_validator("is_faithful", mode="before")
    @classmethod
    def coerce_bool(cls, v: Any) -> bool:
        if isinstance(v, str):
            return v.lower() == "true"
        return bool(v)


class SessionMetadata(BaseModel):
    detected_emotion: EmotionType
    distress_level: int = Field(ge=1, le=5)
    topics_mentioned: list[str] = Field(default_factory=list)
    techniques_suggested: list[str] = Field(default_factory=list)
    crisis_activated: bool

    @field_validator("crisis_activated", mode="before")
    @classmethod
    def coerce_bool(cls, v: Any) -> bool:
        if isinstance(v, str):
            return v.lower() == "true"
        return bool(v)


class ClinicalProfile(BaseModel):
    recurring_topics: dict[str, int] = Field(default_factory=dict)
    total_sessions: int
    crisis_count: int
    avg_distress: float
    techniques_used: list[str] = Field(default_factory=list)
    last_session_date: str
    phq9_score: int | None = None
    phq9_severity: str | None = None
    asq_result: str | None = None
    last_assessment_date: str | None = None


class SessionSummary(BaseModel):
    summary_text: str
    main_topics: list[str] = Field(default_factory=list)
    distress_range: tuple[int, int]
    crisis_triggered: bool
    date: str
