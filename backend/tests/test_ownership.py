from app.database import get_db
from sqlalchemy import select

from app.models import Note, User
from app.ownership import owned_query
from httpx import ASGITransport, AsyncClient


def test_owned_query_cannot_return_another_users_data(test_app) -> None:
    db_generator = test_app.dependency_overrides[get_db]()
    db = next(db_generator)
    first = User(email="first@example.test", role="learner", is_active=True)
    second = User(email="second@example.test", role="learner", is_active=True)
    db.add_all([first, second])
    db.flush()
    db.add_all(
        [
            Note(user_id=first.id, title="First", content="Private"),
            Note(user_id=second.id, title="Second", content="Private"),
        ]
    )
    db.commit()

    visible = db.scalars(
        owned_query(select(Note), Note, first.id)
    ).all()

    assert [note.title for note in visible] == ["First"]


async def test_notes_api_isolates_users(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        first = await client.post(
            "/api/auth/signup",
            json={"email": "first-api@example.test", "password": "a-strong-password"},
        )
        assert first.status_code == 201
        created = await client.post(
            "/api/notes",
            json={"title": "Private", "content": "First user's note"},
        )
        assert created.status_code == 200
        csrf = client.cookies["csrf_token"]
        await client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})

        second = await client.post(
            "/api/auth/signup",
            json={"email": "second-api@example.test", "password": "a-strong-password"},
        )
        assert second.status_code == 201
        notes = await client.get("/api/notes")

    assert notes.status_code == 200
    assert notes.json() == []
