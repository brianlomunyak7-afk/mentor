import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import LearnerProfile
from app.schemas import (
    LearnerProfileResponse,
    LearnerProfileUpdate,
    OnboardingAnswer,
)

router = APIRouter(prefix="/api", tags=["learner"])

ONBOARDING_QUESTIONS = [
    "What do you want to learn?",
    "Why do you want to learn it?",
    "What is your goal?",
    "Do you have a deadline?",
    "What is your current level?",
    "How do you prefer to learn?",
    "How much time can you study per day?",
    "What language should TutorAI use?",
    "Do you have device or internet limits?",
]


def _profile_response(profile: LearnerProfile) -> LearnerProfileResponse:
    try:
        preferences: dict[str, Any] = json.loads(profile.preference_data)
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Learner preferences are corrupted",
        ) from error

    return LearnerProfileResponse(
        learning_topic=profile.learning_topic,
        motivation=profile.motivation,
        goal=profile.goal,
        deadline=profile.deadline,
        current_level=profile.current_level,
        daily_minutes=profile.daily_minutes,
        language=profile.language,
        device_limits=profile.device_limits,
        internet_limits=profile.internet_limits,
        preferences=preferences,
        onboarding_step=profile.onboarding_step,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def _get_profile(db: Session) -> LearnerProfile:
    profile = db.scalar(select(LearnerProfile).order_by(LearnerProfile.id))
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learner profile has not been created",
        )
    return profile


@router.get("/onboarding/questions")
async def get_onboarding_question(db: Session = Depends(get_db)) -> dict[str, Any]:
    profile = db.scalar(select(LearnerProfile).order_by(LearnerProfile.id))
    step = profile.onboarding_step if profile else 0
    return {
        "step": step,
        "question": ONBOARDING_QUESTIONS[step] if step < len(ONBOARDING_QUESTIONS) else None,
        "complete": step >= len(ONBOARDING_QUESTIONS),
    }


@router.post("/onboarding/answers", response_model=LearnerProfileResponse)
async def submit_onboarding_answer(
    answer: OnboardingAnswer,
    db: Session = Depends(get_db),
) -> LearnerProfileResponse:
    profile = db.scalar(select(LearnerProfile).order_by(LearnerProfile.id))
    if profile is None:
        profile = LearnerProfile(language="English", preference_data="{}")
        db.add(profile)
        db.flush()

    if answer.step != profile.onboarding_step:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Expected onboarding step {profile.onboarding_step}",
        )

    value = answer.answer
    if answer.step == 0:
        profile.learning_topic = str(value)
    elif answer.step == 1:
        profile.motivation = str(value)
    elif answer.step == 2:
        profile.goal = str(value)
    elif answer.step == 3:
        profile.deadline = str(value)
    elif answer.step == 4:
        profile.current_level = str(value)
    elif answer.step == 5:
        profile.preference_data = json.dumps({"formats": value})
    elif answer.step == 6:
        try:
            profile.daily_minutes = int(str(value))
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Daily study time must be a whole number of minutes",
            ) from error
    elif answer.step == 7:
        profile.language = str(value)
    elif answer.step == 8:
        profile.device_limits = str(value)
    profile.onboarding_step += 1
    db.commit()
    db.refresh(profile)
    return _profile_response(profile)


@router.get("/profile", response_model=LearnerProfileResponse)
async def get_profile(db: Session = Depends(get_db)) -> LearnerProfileResponse:
    return _profile_response(_get_profile(db))


@router.put("/profile", response_model=LearnerProfileResponse)
async def update_profile(
    updates: LearnerProfileUpdate,
    db: Session = Depends(get_db),
) -> LearnerProfileResponse:
    profile = _get_profile(db)
    values = updates.model_dump(exclude_unset=True)
    preferences = values.pop("preferences", None)
    for field, value in values.items():
        setattr(profile, field, value)
    if preferences is not None:
        profile.preference_data = json.dumps(preferences)
    db.commit()
    db.refresh(profile)
    return _profile_response(profile)
