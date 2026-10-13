from types import SimpleNamespace

from httpx import ASGITransport, AsyncClient

from app.api import router
from app.tutor import answer_question, sanitize_model_text


class FakeProvider:
    provider_name = "fake"
    model_name = "fake-model"

    async def generate(self, messages, *, system_prompt, **kwargs):
        assert messages[-1].content == "Explain loops"
        assert "TutorAI" in system_prompt
        return SimpleNamespace(text="A loop repeats a set of instructions.")


async def test_tutor_service_uses_profile_context(test_app) -> None:
    result = await answer_question(
        FakeProvider(),
        None,
        [],
        "Explain loops",
    )
    assert result == "A loop repeats a set of instructions."


def test_sanitize_model_text_removes_control_characters() -> None:
    assert sanitize_model_text("  safe\x00 answer  ") == "safe answer"


async def test_chat_reports_missing_provider_configuration(test_app, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.create_llm_provider",
        lambda: (_ for _ in ()).throw(ValueError("missing key")),
    )
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/chat",
            json={"message": "Hello"},
        )
    assert response.status_code == 503


async def test_chat_logs_answer_and_supports_report(test_app, monkeypatch) -> None:
    monkeypatch.setattr("app.api.create_llm_provider", lambda: FakeProvider())
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/chat",
            json={"message": "Explain loops"},
        )
        answer_id = response.json()["answer_id"]
        report = await client.post(
            f"/api/chat/{answer_id}/report",
            json={"reason": "This was unclear"},
        )
    assert response.status_code == 200
    assert response.json()["message"].startswith("A loop")
    assert report.status_code == 204
