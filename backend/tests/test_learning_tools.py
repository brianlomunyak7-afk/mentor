from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.models import Lesson, User
from app.rate_limit import InMemoryRateLimiter


def test_rate_limiter_blocks_after_limit() -> None:
    limiter = InMemoryRateLimiter(limit=2)
    assert limiter.is_allowed("test-client")
    assert limiter.is_allowed("test-client")
    assert not limiter.is_allowed("test-client")
    assert limiter.is_allowed("other-client")


async def test_notes_bookmarks_progress_and_export(test_app, authenticated_client) -> None:
    db_generator = test_app.dependency_overrides[get_db]()
    db = next(db_generator)
    user = db.query(User).filter(User.email == "test@example.com").one()
    lesson = Lesson(
        user_id=user.id,
        plan_id=1,
        module_number=1,
        lesson_number=1,
        title="Variables",
        goal="Learn variables",
        explanation="Explain",
        examples_json='["x = 1", "y = 2"]',
        practice_task="Practice",
        quiz_json='["What is x?"]',
        estimated_minutes=20,
        status="not_started",
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    note = await authenticated_client.post(
        "/api/notes",
        json={"title": "Reminder", "content": "Review variables"},
    )
    bookmark = await authenticated_client.post(
        "/api/bookmarks",
        json={
            "title": "Python docs",
            "url": "https://docs.python.org",
            "source": "official",
        },
    )
    quiz = await authenticated_client.post(
        f"/api/lessons/{lesson.id}/quiz",
        json={"answers": []},
    )
    progress = await authenticated_client.get("/api/progress")
    export = await authenticated_client.get("/api/export")

    assert note.status_code == 200
    assert bookmark.status_code == 200
    assert quiz.status_code == 422
    assert progress.json()["lessons_total"] == 1
    assert "notes" in export.json()
    assert "bookmarks" in export.json()
