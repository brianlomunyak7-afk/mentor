import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Bookmark, Lesson, LearningPlan, Note


def export_learning_data(db: Session) -> dict[str, object]:
    plans = db.scalars(select(LearningPlan).order_by(LearningPlan.id)).all()
    lessons = db.scalars(select(Lesson).order_by(Lesson.id)).all()
    notes = db.scalars(select(Note).order_by(Note.id)).all()
    bookmarks = db.scalars(select(Bookmark).order_by(Bookmark.id)).all()
    return {
        "exported_at": datetime.now().isoformat(),
        "plans": [
            {"id": plan.id, "title": plan.title, "goal": plan.goal, "status": plan.status}
            for plan in plans
        ],
        "lessons": [
            {
                "id": lesson.id,
                "plan_id": lesson.plan_id,
                "title": lesson.title,
                "status": lesson.status,
            }
            for lesson in lessons
        ],
        "notes": [
            {"id": note.id, "title": note.title, "content": note.content}
            for note in notes
        ],
        "bookmarks": [
            {"id": bookmark.id, "title": bookmark.title, "url": bookmark.url}
            for bookmark in bookmarks
        ],
    }


def export_learning_data_json(db: Session) -> str:
    return json.dumps(export_learning_data(db), indent=2)
