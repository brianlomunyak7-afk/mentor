import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import AuthSession, User

password_hasher = PasswordHasher()
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _access_token(user: User) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user.id), "role": user.role, "type": "access",
         "iat": now, "exp": now + timedelta(minutes=settings.access_token_minutes)},
        settings.jwt_secret,
        algorithm="HS256",
    )


def _new_session(user: User, request: Request, db: Session) -> tuple[str, str]:
    settings = get_settings()
    refresh_token = secrets.token_urlsafe(48)
    session = AuthSession(
        user_id=user.id,
        refresh_token_hash=_token_hash(refresh_token),
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days),
    )
    db.add(session)
    return refresh_token, _access_token(user)


def set_auth_cookies(response, access_token: str, refresh_token: str, csrf_token: str) -> None:
    settings = get_settings()
    cookie_options = {
        "httponly": True,
        "secure": settings.secure_cookies,
        "samesite": "lax",
        "path": "/",
    }
    response.set_cookie("access_token", access_token, max_age=settings.access_token_minutes * 60, **cookie_options)
    response.set_cookie("refresh_token", refresh_token, max_age=settings.refresh_token_days * 86400, **cookie_options)
    response.set_cookie("csrf_token", csrf_token, httponly=False, max_age=settings.refresh_token_days * 86400,
                        secure=settings.secure_cookies, samesite="lax", path="/")


def clear_auth_cookies(response) -> None:
    for name in ("access_token", "refresh_token", "csrf_token"):
        response.delete_cookie(name, path="/")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise ValueError
        user = db.get(User, int(payload["sub"]))
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        user = None
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


def require_csrf(request: Request) -> None:
    cookie_token = request.cookies.get("csrf_token")
    header_token = request.headers.get("x-csrf-token")
    if not cookie_token or not header_token or not secrets.compare_digest(cookie_token, header_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")


def authenticate(email: str, password: str, request: Request, db: Session) -> tuple[User, str, str]:
    user = db.scalar(select(User).where(User.email == normalize_email(email)))
    now = datetime.now(timezone.utc)
    if user is None or (user.locked_until and user.locked_until > now):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if user.password_hash is None or not verify_password(user.password_hash, password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
            user.failed_login_attempts = 0
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    user.failed_login_attempts = 0
    user.locked_until = None
    refresh_token, access_token = _new_session(user, request, db)
    db.commit()
    return user, access_token, refresh_token
