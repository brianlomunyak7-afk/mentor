import json
from datetime import datetime, timezone
from typing import Any

from fastapi.responses import Response
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.llm.base import LLMProviderError
from app.llm.factory import create_llm_provider
from app.models import (
    Bookmark,
    LearningPlan,
    LearnerProfile,
    Lesson,
    Note,
    QuizAttempt,
    Resource,
    TutorAnswerLog,
)
from app.plan import generate_plan
from app.schemas import (
    ChatRequest,
    ChatResponse,
    LearnerProfileResponse,
    LearnerProfileUpdate,
    LearningPlanResponse,
    LessonProgressUpdate,
    LessonResponse,
    ResourceResponse,
    BookmarkRequest,
    BookmarkResponse,
    NoteRequest,
    NoteResponse,
    ProgressSummary,
    QuizResult,
    QuizSubmission,
    OnboardingAnswer,
    WrongAnswerReport,
)
from app.tutor import answer_question
from app.resources import ResourceSearchError, find_resources
from app.export import export_learning_data_json

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


def _lesson_response(lesson: Lesson) -> LessonResponse:
    return LessonResponse(
        id=lesson.id,
        module_number=lesson.module_number,
        lesson_number=lesson.lesson_number,
        title=lesson.title,
        goal=lesson.goal,
        explanation=lesson.explanation,
        examples=json.loads(lesson.examples_json),
        practice_task=lesson.practice_task,
        quiz=json.loads(lesson.quiz_json),
        estimated_minutes=lesson.estimated_minutes,
        status=lesson.status,
    )


def _plan_response(plan: LearningPlan, lessons: list[Lesson]) -> LearningPlanResponse:
    return LearningPlanResponse(
        id=plan.id,
        title=plan.title,
        goal=plan.goal,
        status=plan.status,
        lessons=[_lesson_response(lesson) for lesson in lessons],
    )


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


@router.post("/chat", response_model=ChatResponse, tags=["tutor"])
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    try:
        provider = create_llm_provider()
        answer = await answer_question(
            provider,
            db.scalar(select(LearnerProfile).order_by(LearnerProfile.id)),
            request.history,
            request.message,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TutorAI is not configured with a valid model provider",
        ) from error
    except LLMProviderError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The configured model provider could not answer right now",
        ) from error

    log = TutorAnswerLog(
        user_message=request.message,
        assistant_message=answer,
        provider=provider.provider_name,
        model=provider.model_name,
        sources_json="[]",
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return ChatResponse(
        answer_id=log.id,
        message=answer,
        provider=provider.provider_name,
        model=provider.model_name,
        sources=[],
    )


@router.post("/chat/{answer_id}/report", status_code=status.HTTP_204_NO_CONTENT)
async def report_wrong_answer(
    answer_id: int,
    report: WrongAnswerReport,
    db: Session = Depends(get_db),
) -> None:
    log = db.get(TutorAnswerLog, answer_id)
    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor answer was not found",
        )
    log.reported_wrong = True
    db.commit()


@router.post("/plans", response_model=LearningPlanResponse, tags=["learning plan"])
async def create_learning_plan(
    db: Session = Depends(get_db),
) -> LearningPlanResponse:
    profile = _get_profile(db)
    try:
        provider = create_llm_provider()
        generated = await generate_plan(provider, profile)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TutorAI could not create a valid learning plan",
        ) from error
    except LLMProviderError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The configured model provider could not create a plan",
        ) from error

    plan = LearningPlan(
        title=generated.title,
        goal=profile.goal or profile.learning_topic or "Learning goal",
        status="active",
    )
    db.add(plan)
    db.flush()
    lessons: list[Lesson] = []
    for module_number, module in enumerate(generated.modules, start=1):
        for lesson_number, lesson in enumerate(module.lessons, start=1):
            stored = Lesson(
                plan_id=plan.id,
                module_number=module_number,
                lesson_number=lesson_number,
                title=lesson.title,
                goal=lesson.goal,
                explanation=lesson.explanation,
                examples_json=json.dumps(lesson.examples),
                practice_task=lesson.practice_task,
                quiz_json=json.dumps(lesson.quiz),
                estimated_minutes=lesson.estimated_minutes,
                status="not_started",
            )
            db.add(stored)
            lessons.append(stored)
    db.commit()
    for lesson in lessons:
        db.refresh(lesson)
    db.refresh(plan)
    return _plan_response(plan, lessons)


@router.get("/plans/latest", response_model=LearningPlanResponse, tags=["learning plan"])
async def get_latest_learning_plan(
    db: Session = Depends(get_db),
) -> LearningPlanResponse:
    plan = db.scalar(select(LearningPlan).order_by(LearningPlan.id.desc()))
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No learning plan has been created",
        )
    lessons = list(
        db.scalars(
            select(Lesson)
            .where(Lesson.plan_id == plan.id)
            .order_by(Lesson.module_number, Lesson.lesson_number)
        )
    )
    return _plan_response(plan, lessons)


@router.patch(
    "/lessons/{lesson_id}/progress",
    response_model=LessonResponse,
    tags=["learning plan"],
)
async def update_lesson_progress(
    lesson_id: int,
    update: LessonProgressUpdate,
    db: Session = Depends(get_db),
) -> LessonResponse:
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson was not found",
        )
    lesson.status = update.status
    lesson.completed_at = (
        datetime.now(timezone.utc) if update.status == "completed" else None
    )
    db.commit()
    db.refresh(lesson)
    return _lesson_response(lesson)


@router.get(
    "/lessons/{lesson_id}/resources",
    response_model=list[ResourceResponse],
    tags=["resources"],
)
async def get_lesson_resources(
    lesson_id: int,
    db: Session = Depends(get_db),
) -> list[ResourceResponse]:
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson was not found",
        )
    profile = _get_profile(db)
    try:
        candidates = await find_resources(lesson, profile)
    except ResourceSearchError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Resource search is temporarily unavailable",
        ) from error

    db.query(Resource).filter(Resource.lesson_id == lesson.id).delete()
    stored: list[Resource] = []
    for candidate in candidates:
        resource = Resource(
            lesson_id=lesson.id,
            title=candidate.title,
            url=candidate.url,
            source=candidate.source,
            duration_seconds=candidate.duration_seconds,
            reason=candidate.reason,
            credibility_score=candidate.credibility_score,
            relevance_score=candidate.relevance_score,
        )
        db.add(resource)
        stored.append(resource)
    db.commit()
    return [
        ResourceResponse(
            title=item.title,
            url=item.url,
            source=item.source,
            duration_seconds=item.duration_seconds,
            reason=item.reason,
        )
        for item in stored
    ]


@router.post("/notes", response_model=NoteResponse, tags=["notes"])
async def create_note(note: NoteRequest, db: Session = Depends(get_db)) -> NoteResponse:
    stored = Note(**note.model_dump())
    db.add(stored)
    db.commit()
    db.refresh(stored)
    return NoteResponse.model_validate(stored, from_attributes=True)


@router.get("/notes", response_model=list[NoteResponse], tags=["notes"])
async def list_notes(db: Session = Depends(get_db)) -> list[NoteResponse]:
    notes = db.scalars(select(Note).order_by(Note.updated_at.desc())).all()
    return [NoteResponse.model_validate(note, from_attributes=True) for note in notes]


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["notes"])
async def delete_note(note_id: int, db: Session = Depends(get_db)) -> None:
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note was not found")
    db.delete(note)
    db.commit()


@router.post("/bookmarks", response_model=BookmarkResponse, tags=["bookmarks"])
async def create_bookmark(
    bookmark: BookmarkRequest,
    db: Session = Depends(get_db),
) -> BookmarkResponse:
    stored = Bookmark(**bookmark.model_dump())
    db.add(stored)
    db.commit()
    db.refresh(stored)
    return BookmarkResponse.model_validate(stored, from_attributes=True)


@router.get("/bookmarks", response_model=list[BookmarkResponse], tags=["bookmarks"])
async def list_bookmarks(db: Session = Depends(get_db)) -> list[BookmarkResponse]:
    bookmarks = db.scalars(select(Bookmark).order_by(Bookmark.created_at.desc())).all()
    return [
        BookmarkResponse.model_validate(bookmark, from_attributes=True)
        for bookmark in bookmarks
    ]


@router.delete(
    "/bookmarks/{bookmark_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["bookmarks"],
)
async def delete_bookmark(bookmark_id: int, db: Session = Depends(get_db)) -> None:
    bookmark = db.get(Bookmark, bookmark_id)
    if bookmark is None:
        raise HTTPException(status_code=404, detail="Bookmark was not found")
    db.delete(bookmark)
    db.commit()


@router.post(
    "/lessons/{lesson_id}/quiz",
    response_model=QuizResult,
    tags=["learning plan"],
)
async def submit_quiz(
    lesson_id: int,
    submission: QuizSubmission,
    db: Session = Depends(get_db),
) -> QuizResult:
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson was not found")
    questions = json.loads(lesson.quiz_json)
    total = len(questions)
    score = min(len(submission.answers), total)
    feedback = (
        "Strong work. Keep going and revisit this lesson later."
        if score == total
        else "This topic may need another explanation. Review the examples and try again."
    )
    attempt = QuizAttempt(
        lesson_id=lesson.id,
        score=score,
        total=total,
        feedback=feedback,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return QuizResult(
        attempt_id=attempt.id,
        score=score,
        total=total,
        feedback=feedback,
    )


@router.get("/progress", response_model=ProgressSummary, tags=["progress"])
async def get_progress(db: Session = Depends(get_db)) -> ProgressSummary:
    lessons = list(db.scalars(select(Lesson)))
    completed = sum(lesson.status == "completed" for lesson in lessons)
    attempts = list(db.scalars(select(QuizAttempt).order_by(QuizAttempt.created_at.desc())))
    weak_area = None
    if attempts and attempts[0].score < attempts[0].total:
        lesson = db.get(Lesson, attempts[0].lesson_id)
        weak_area = lesson.title if lesson else None
    return ProgressSummary(
        lessons_completed=completed,
        lessons_total=len(lessons),
        completion_percent=round(completed / len(lessons) * 100) if lessons else 0,
        streak_days=1 if completed else 0,
        weak_area=weak_area,
    )


@router.get("/export", tags=["progress"])
async def export_data(db: Session = Depends(get_db)) -> Response:
    return Response(
        content=export_learning_data_json(db),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="tutorai-export.json"'},
    )
