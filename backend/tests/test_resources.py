import httpx

from app.config import Settings
from app.database import get_db
from app.models import LearnerProfile, Lesson, User
from app.resources import ResourceCandidate, find_resources


async def test_resource_search_uses_api_results_and_drops_broken_links() -> None:
    calls: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if request.url.host == "www.googleapis.com":
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "id": {"videoId": "abc"},
                            "snippet": {
                                "title": "Python lesson",
                                "channelTitle": "Official channel",
                            },
                        }
                    ]
                },
            )
        if request.method == "HEAD":
            return httpx.Response(200)
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        candidates = await find_resources(
            Lesson(id=1, plan_id=1, module_number=1, lesson_number=1,
                   title="Variables", goal="Learn variables", explanation="Explain",
                   examples_json="[]", practice_task="Practice", quiz_json="[]",
                   estimated_minutes=20, status="not_started"),
            LearnerProfile(learning_topic="Python", language="English"),
            settings=Settings(youtube_api_key="test-key"),
            client=client,
        )

    assert len(candidates) == 1
    assert candidates[0].url == "https://www.youtube.com/watch?v=abc"
    assert any("youtube/v3/search" in call for call in calls)


async def test_resources_route_returns_checked_candidates(
    test_app,
    authenticated_client,
    monkeypatch,
) -> None:
    candidate = ResourceCandidate(
        title="Python guide",
        url="https://docs.example.test/python",
        source="tavily",
        duration_seconds=None,
        reason="A relevant guide",
        credibility_score=0.8,
        relevance_score=0.9,
    )

    async def fake_find_resources(lesson, profile):
        return [candidate]

    monkeypatch.setattr("app.api.find_resources", fake_find_resources)
    db_generator = test_app.dependency_overrides[get_db]()
    db = next(db_generator)
    user = db.query(User).filter(User.email == "test@example.com").one()
    db.add(LearnerProfile(user_id=user.id, learning_topic="Python", language="English"))
    lesson = Lesson(
        user_id=user.id,
        plan_id=1,
        module_number=1,
        lesson_number=1,
        title="Variables",
        goal="Learn variables",
        explanation="Explain",
        examples_json="[]",
        practice_task="Practice",
        quiz_json="[]",
        estimated_minutes=20,
        status="not_started",
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    response = await authenticated_client.get(f"/api/lessons/{lesson.id}/resources")

    assert response.status_code == 200
    assert response.json()[0]["url"] == candidate.url
