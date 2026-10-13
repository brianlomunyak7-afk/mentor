from app.database import get_db
from sqlalchemy import select

from app.models import Note, User
from app.ownership import owned_query


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
