from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, model_validator

from logic_graph.api.deps import get_store
from logic_graph.auth import User, current_active_user
from logic_graph.memory.long_term import load_profile, save_profile
from logic_graph.models import ClinicalProfile

router = APIRouter(prefix="/assessments", tags=["assessments"])

_PHQ9_SEVERITY = [
    (4, "minimal"),
    (9, "mild"),
    (14, "moderate"),
    (19, "moderately_severe"),
]


def _score_phq9(answers: list[int]) -> tuple[int, str]:
    score = sum(answers)
    for threshold, label in _PHQ9_SEVERITY:
        if score <= threshold:
            return score, label
    return score, "severe"


def _score_asq(answers: list[bool], acuity: bool | None) -> str:
    if not any(answers):
        return "negative"
    return "positive_acute" if acuity else "positive_non_acute"


class AssessmentSubmission(BaseModel):
    phq9_answers: list[int]
    asq_answers: list[bool]
    asq_acuity_answer: bool | None = None

    @model_validator(mode="after")
    def validate_answers(self) -> "AssessmentSubmission":
        if len(self.phq9_answers) != 9:
            raise ValueError("phq9_answers must have exactly 9 items")
        if any(v < 0 or v > 3 for v in self.phq9_answers):
            raise ValueError("phq9_answers values must be between 0 and 3")
        if len(self.asq_answers) != 4:
            raise ValueError("asq_answers must have exactly 4 items")
        if any(self.asq_answers) and self.asq_acuity_answer is None:
            raise ValueError("asq_acuity_answer is required when any asq_answers is True")
        return self


class AssessmentStatus(BaseModel):
    needed: bool
    phq9_score: int | None = None
    phq9_severity: str | None = None
    asq_result: str | None = None


class AssessmentResult(BaseModel):
    phq9_score: int
    phq9_severity: str
    asq_result: str


@router.get("/status", response_model=AssessmentStatus)
async def assessment_status(
    user: User = Depends(current_active_user),
    store=Depends(get_store),
) -> AssessmentStatus:
    today = datetime.now().strftime("%Y-%m-%d")
    profile_data = await load_profile(store, str(user.id))

    if not profile_data:
        return AssessmentStatus(needed=True)

    profile = ClinicalProfile(**profile_data)
    if profile.last_assessment_date != today:
        return AssessmentStatus(needed=True)

    return AssessmentStatus(
        needed=False,
        phq9_score=profile.phq9_score,
        phq9_severity=profile.phq9_severity,
        asq_result=profile.asq_result,
    )


@router.post("/submit", response_model=AssessmentResult)
async def submit_assessments(
    submission: AssessmentSubmission,
    user: User = Depends(current_active_user),
    store=Depends(get_store),
) -> AssessmentResult:
    phq9_score, phq9_severity = _score_phq9(submission.phq9_answers)
    asq_result = _score_asq(submission.asq_answers, submission.asq_acuity_answer)

    profile_data = await load_profile(store, str(user.id))
    if profile_data:
        profile = ClinicalProfile(**profile_data)
    else:
        profile = ClinicalProfile(
            recurring_topics={},
            total_sessions=0,
            crisis_count=0,
            avg_distress=0.0,
            techniques_used=[],
            last_session_date="",
        )

    updated = profile.model_copy(update={
        "phq9_score": phq9_score,
        "phq9_severity": phq9_severity,
        "asq_result": asq_result,
        "last_assessment_date": datetime.now().strftime("%Y-%m-%d"),
    })

    await save_profile(store, str(user.id), updated.model_dump())

    return AssessmentResult(
        phq9_score=phq9_score,
        phq9_severity=phq9_severity,
        asq_result=asq_result,
    )
