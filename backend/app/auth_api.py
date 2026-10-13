import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import (
    _new_session,
    _token_hash,
    _utc,
    authenticate,
    clear_auth_cookies,
    get_current_user,
    hash_password,
    normalize_email,
    require_csrf,
    set_auth_cookies,
)
from app.database import get_db
from app.models import AuthSession, User
from app.schemas import (
    AuthUserResponse,
    LoginRequest,
    SessionResponse,
    SignupRequest,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_response(user: User) -> AuthUserResponse:
    return AuthUserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        email_verified=user.email_verified,
    )


@router.post("/signup", response_model=AuthUserResponse, status_code=201)
async def signup(
    payload: SignupRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthUserResponse:
    email = normalize_email(payload.email)
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="An account with that email already exists")
    user = User(email=email, password_hash=hash_password(payload.password), role="learner")
    db.add(user)
    db.flush()
    refresh_token, access_token = _new_session(user, request, db)
    db.commit()
    set_auth_cookies(response, access_token, refresh_token, secrets.token_urlsafe(32))
    return _user_response(user)


@router.post("/login", response_model=AuthUserResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthUserResponse:
    user, access_token, refresh_token = authenticate(payload.email, payload.password, request, db)
    set_auth_cookies(response, access_token, refresh_token, secrets.token_urlsafe(32))
    return _user_response(user)


@router.post("/refresh", response_model=AuthUserResponse)
async def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthUserResponse:
    require_csrf(request)
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    session = db.scalar(
        select(AuthSession).where(
            AuthSession.refresh_token_hash == _token_hash(token),
            AuthSession.revoked_at.is_(None),
        )
    )
    now = datetime.now(timezone.utc)
    if session is None or _utc(session.expires_at) <= now:
        raise HTTPException(status_code=401, detail="Refresh session is invalid")
    user = db.get(User, session.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Authentication required")
    session.revoked_at = now
    new_refresh, access = _new_session(user, request, db)
    db.commit()
    set_auth_cookies(response, access, new_refresh, secrets.token_urlsafe(32))
    return _user_response(user)


@router.get("/me", response_model=AuthUserResponse)
async def me(user: User = Depends(get_current_user)) -> AuthUserResponse:
    return _user_response(user)


@router.get("/sessions", response_model=list[SessionResponse])
async def sessions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SessionResponse]:
    records = db.scalars(
        select(AuthSession)
        .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
        .order_by(AuthSession.created_at.desc())
    ).all()
    return [SessionResponse.model_validate(record, from_attributes=True) for record in records]


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    require_csrf(request)
    token = request.cookies.get("refresh_token")
    if token:
        session = db.scalar(select(AuthSession).where(AuthSession.refresh_token_hash == _token_hash(token)))
        if session and session.user_id == user.id:
            session.revoked_at = datetime.now(timezone.utc)
            db.commit()
    clear_auth_cookies(response)


@router.post("/logout-everywhere", status_code=204)
async def logout_everywhere(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    require_csrf(request)
    db.query(AuthSession).filter(
        AuthSession.user_id == user.id,
        AuthSession.revoked_at.is_(None),
    ).update({"revoked_at": datetime.now(timezone.utc)})
    db.commit()
    clear_auth_cookies(response)
