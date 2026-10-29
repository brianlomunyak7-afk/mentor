from httpx import ASGITransport, AsyncClient


async def test_onboarding_accepts_one_answer_at_a_time(authenticated_client) -> None:
    question = await authenticated_client.get("/api/onboarding/questions")
    answer = await authenticated_client.post(
        "/api/onboarding/answers",
        json={"step": 0, "answer": "Python"},
    )

    assert question.json() == {
        "step": 0,
        "question": "What do you want to learn?",
        "complete": False,
    }
    assert answer.status_code == 200
    assert answer.json()["learning_topic"] == "Python"
    assert answer.json()["onboarding_step"] == 1


async def test_profile_requires_onboarding_first(authenticated_client) -> None:
    response = await authenticated_client.get("/api/profile")

    assert response.status_code == 404
