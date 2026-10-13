from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import User


def get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User was not found",
        )
    return user


def owned_query(statement: Select, model: type, user_id: int) -> Select:
    if not hasattr(model, "user_id"):
        raise TypeError(f"{model.__name__} does not support ownership filtering")
    return statement.where(model.user_id == user_id)
