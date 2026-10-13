from types import SimpleNamespace

from httpx import ASGITransport, AsyncClient


VALID_PLAN = """{
  "title": "Python foundations",
  "modules": [{
    "title": "Core concepts",
    "lessons": [{
      "title": "Variables",
      "goal": "Store and use values",
      "explanation": "A variable gives a name to a value.",
      "examples": ["name = 'Ada'", "age = 36"],
      "practice_task": "Create three variables about yourself.",
      "quiz": ["What does a variable name?"],
      "estimated_minutes": 25
    }]
  }]
}"""


class PlanProvider:
    provider_name = "fake"
    model_name = "fake-plan-model"

    async def generate(self, messages, *, system_prompt, **kwargs):
        return SimpleNamespace(text=VALID_PLAN)


async def test_create_and_update_learning_plan(test_app, monkeypatch) -> None:
    monkeypatch.setattr("app.api.create_llm_provider", lambda: PlanProvider())
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        await client.post(
            "/api/onboarding/answers",
            json={"step": 0, "answer": "Python"},
        )
        response = await client.post("/api/plans")
        lesson_id = response.json()["lessons"][0]["id"]
        progress = await client.patch(
            f"/api/lessons/{lesson_id}/progress",
            json={"status": "completed"},
        )
        latest = await client.get("/api/plans/latest")

    assert response.status_code == 200
    assert response.json()["title"] == "Python foundations"
    assert progress.json()["status"] == "completed"
    assert latest.json()["lessons"][0]["status"] == "completed"


async def test_plan_rejects_malformed_model_output(test_app, monkeypatch) -> None:
    class InvalidProvider(PlanProvider):
        async def generate(self, messages, *, system_prompt, **kwargs):
            return SimpleNamespace(text='{"title": "Missing modules"}')

    monkeypatch.setattr("app.api.create_llm_provider", lambda: InvalidProvider())
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        await client.post(
            "/api/onboarding/answers",
            json={"step": 0, "answer": "Python"},
        )
        response = await client.post("/api/plans")

    assert response.status_code == 503
    assert "valid learning plan" in response.json()["detail"]
