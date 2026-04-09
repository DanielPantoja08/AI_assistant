"""Tests for Pydantic models and enum validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from logic_graph.models import (
    ClinicalProfile,
    CrisisAssessment,
    CrisisLevel,
    EmotionType,
    HallucinationGrade,
    SessionMetadata,
)


# ---------------------------------------------------------------------------
# CrisisAssessment
# ---------------------------------------------------------------------------


def test_crisis_assessment_valid():
    ca = CrisisAssessment(
        is_crisis=True,
        crisis_level=CrisisLevel.high,
        risk_indicators=["suicidal ideation"],
        reasoning="explicit mention",
    )
    assert ca.is_crisis is True
    assert ca.crisis_level == CrisisLevel.high
    assert ca.risk_indicators == ["suicidal ideation"]


def test_crisis_assessment_default_risk_indicators():
    ca = CrisisAssessment(
        is_crisis=False, crisis_level=CrisisLevel.none, reasoning="no risk"
    )
    assert ca.risk_indicators == []


# ---------------------------------------------------------------------------
# HallucinationGrade
# ---------------------------------------------------------------------------


def test_hallucination_grade_faithful():
    hg = HallucinationGrade(is_faithful=True, reasoning="grounded in docs")
    assert hg.is_faithful is True
    assert hg.unfaithful_claims == []


def test_hallucination_grade_with_claims():
    hg = HallucinationGrade(
        is_faithful=False,
        unfaithful_claims=["made up statistic"],
        reasoning="not in source",
    )
    assert hg.unfaithful_claims == ["made up statistic"]


# ---------------------------------------------------------------------------
# SessionMetadata
# ---------------------------------------------------------------------------


def test_session_metadata_valid():
    sm = SessionMetadata(
        detected_emotion=EmotionType.anxious,
        distress_level=4,
        topics_mentioned=["sleep"],
        techniques_suggested=["breathing"],
        crisis_activated=False,
    )
    assert sm.detected_emotion == EmotionType.anxious
    assert sm.distress_level == 4


def test_session_metadata_distress_below_minimum():
    with pytest.raises(ValidationError):
        SessionMetadata(
            detected_emotion=EmotionType.neutral,
            distress_level=0,
            crisis_activated=False,
        )


def test_session_metadata_distress_above_maximum():
    with pytest.raises(ValidationError):
        SessionMetadata(
            detected_emotion=EmotionType.neutral,
            distress_level=6,
            crisis_activated=False,
        )


def test_session_metadata_distress_boundary_min():
    sm = SessionMetadata(
        detected_emotion=EmotionType.calm, distress_level=1, crisis_activated=False
    )
    assert sm.distress_level == 1


def test_session_metadata_distress_boundary_max():
    sm = SessionMetadata(
        detected_emotion=EmotionType.sad, distress_level=5, crisis_activated=True
    )
    assert sm.distress_level == 5


def test_session_metadata_default_lists():
    sm = SessionMetadata(
        detected_emotion=EmotionType.neutral, distress_level=3, crisis_activated=False
    )
    assert sm.topics_mentioned == []
    assert sm.techniques_suggested == []


# ---------------------------------------------------------------------------
# ClinicalProfile
# ---------------------------------------------------------------------------


def test_clinical_profile_defaults():
    cp = ClinicalProfile(
        total_sessions=0,
        crisis_count=0,
        avg_distress=0.0,
        last_session_date="",
    )
    assert cp.recurring_topics == {}
    assert cp.techniques_used == []


def test_clinical_profile_with_data():
    cp = ClinicalProfile(
        recurring_topics={"ansiedad": 3, "sueno": 1},
        total_sessions=5,
        crisis_count=1,
        avg_distress=3.2,
        techniques_used=["breathing", "journaling"],
        last_session_date="2026-03-29",
    )
    assert cp.recurring_topics["ansiedad"] == 3
    assert cp.total_sessions == 5
    assert len(cp.techniques_used) == 2
