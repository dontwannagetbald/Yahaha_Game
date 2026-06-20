from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session
from app.models import OAuthAccount, Session, User
from app.schemas import (
    AvatarUploadCompleteRequest,
    AvatarUploadCompleteResponse,
    AvatarUploadPresignRequest,
    AvatarUploadPresignResponse,
    AuthResponse,
    LoginRequest,
    MessageResponse,
    OAuthStartResponse,
    RegisterRequest,
    UserResponse,
)
from app.security import hash_password, verify_password
from app.storage import ObjectStorageService


router = APIRouter(prefix="/api/auth", tags=["auth"])
MAX_AVATAR_UPLOAD_SIZE_BYTES = 2 * 1024 * 1024
ALLOWED_AVATAR_MIME_TYPES = {"image/png", "image/jpeg", "image/webp"}


def get_storage_service() -> ObjectStorageService:
    return ObjectStorageService(settings)


def serialize_user(user: User) -> UserResponse:
    return UserResponse(
        user_id=str(user.user_id),
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
    )


def session_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=settings.session_ttl_seconds)


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def set_session_cookie(response: Response, session_id: uuid.UUID) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        str(session_id),
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        max_age=settings.session_ttl_seconds,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(settings.session_cookie_name, path="/")


async def create_session(
    db: AsyncSession, user: User, request: Request, response: Response
) -> None:
    session = Session(
        user_id=user.user_id,
        expires_at=session_expiry(),
        last_seen_at=datetime.now(timezone.utc),
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    db.add(session)
    await db.flush()
    set_session_cookie(response, session.session_id)


async def get_current_user(
    request: Request, db: Annotated[AsyncSession, Depends(get_session)]
) -> User:
    user = await get_optional_current_user(request, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def get_optional_current_user(
    request: Request, db: AsyncSession
) -> User | None:
    raw_session_id = request.cookies.get(settings.session_cookie_name)
    if not raw_session_id:
        return None
    try:
        session_id = uuid.UUID(raw_session_id)
    except ValueError:
        return None

    result = await db.execute(
        select(Session, User)
        .join(User, User.user_id == Session.user_id)
        .where(Session.session_id == session_id)
    )
    row = result.first()
    if row is None:
        return None

    session, user = row
    if normalize_datetime(session.expires_at) <= datetime.now(timezone.utc):
        await db.delete(session)
        await db.commit()
        return None

    session.last_seen_at = datetime.now(timezone.utc)
    await db.commit()
    return user


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> AuthResponse:
    email = payload.email.lower()
    existing = await db.execute(
        select(User).where(User.email == email, User.password_hash.is_not(None))
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email is already registered")

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name or email.split("@", 1)[0],
        avatar_url=payload.avatar_url,
    )
    db.add(user)
    await db.flush()
    await create_session(db, user, request, response)
    await db.commit()
    return AuthResponse(user=serialize_user(user))


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> AuthResponse:
    email = payload.email.lower()
    result = await db.execute(
        select(User).where(User.email == email, User.password_hash.is_not(None))
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    await create_session(db, user, request, response)
    await db.commit()
    return AuthResponse(user=serialize_user(user))


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> MessageResponse:
    raw_session_id = request.cookies.get(settings.session_cookie_name)
    if raw_session_id:
        try:
            session_id = uuid.UUID(raw_session_id)
        except ValueError:
            session_id = None
        if session_id:
            result = await db.execute(
                select(Session).where(Session.session_id == session_id)
            )
            session = result.scalar_one_or_none()
            if session:
                await db.delete(session)
                await db.commit()
    clear_session_cookie(response)
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=AuthResponse)
async def me(user: Annotated[User, Depends(get_current_user)]) -> AuthResponse:
    return AuthResponse(user=serialize_user(user))


@router.post("/avatar/presign", response_model=AvatarUploadPresignResponse)
async def presign_registration_avatar(
    payload: AvatarUploadPresignRequest,
    storage: Annotated[ObjectStorageService, Depends(get_storage_service)],
) -> AvatarUploadPresignResponse:
    if payload.mime_type not in ALLOWED_AVATAR_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Avatar must be png, jpg, or webp")
    if payload.size_bytes > MAX_AVATAR_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Avatar exceeds 2MB limit")

    upload_id = uuid.uuid4()
    object_key = storage.build_registration_avatar_object_key(
        upload_id=upload_id,
        filename=payload.filename,
    )
    presigned = storage.build_presigned_upload_url(object_key)
    return AvatarUploadPresignResponse(
        upload_id=str(upload_id),
        object_key=object_key,
        upload_url=presigned.url,
        expires_in=presigned.expires_in,
    )


@router.post("/avatar/complete", response_model=AvatarUploadCompleteResponse)
async def complete_registration_avatar(
    payload: AvatarUploadCompleteRequest,
    storage: Annotated[ObjectStorageService, Depends(get_storage_service)],
) -> AvatarUploadCompleteResponse:
    expected_prefix = f"avatars/registrations/{payload.upload_id}/"
    if not payload.object_key.startswith(expected_prefix):
        raise HTTPException(status_code=403, detail="Avatar upload does not match upload id")
    if payload.mime_type not in ALLOWED_AVATAR_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Avatar must be png, jpg, or webp")
    return AvatarUploadCompleteResponse(
        avatar_url=storage.build_public_read_url(payload.object_key)
    )


def build_google_auth_url(state: str) -> str:
    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "select_account",
        }
    )
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"


@router.get("/oauth/google/start", response_model=OAuthStartResponse)
async def google_start(response: Response) -> OAuthStartResponse:
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    state = secrets.token_urlsafe(32)
    response.set_cookie(
        settings.oauth_state_cookie_name,
        state,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        max_age=600,
        path="/",
    )
    return OAuthStartResponse(authorization_url=build_google_auth_url(state))


async def fetch_google_profile(code: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_response.status_code >= 400:
            raise HTTPException(status_code=401, detail="Google token exchange failed")
        token = token_response.json()
        user_response = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {token['access_token']}"},
        )
        if user_response.status_code >= 400:
            raise HTTPException(status_code=401, detail="Google profile fetch failed")
        return user_response.json()


async def login_or_create_oauth_user(
    db: AsyncSession, profile: dict, provider: str
) -> User:
    provider_user_id = profile.get("sub")
    provider_email = profile.get("email")
    email_verified = profile.get("email_verified") is True
    if not provider_user_id:
        raise HTTPException(status_code=401, detail="OAuth profile is missing user id")
    if not provider_email or not email_verified:
        raise HTTPException(status_code=401, detail="OAuth email is missing or unverified")

    result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id,
        )
    )
    oauth_account = result.scalar_one_or_none()
    if oauth_account:
        user = await db.get(User, oauth_account.user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="OAuth account is orphaned")
        oauth_account.provider_email = provider_email.lower()
        oauth_account.provider_name = profile.get("name")
        oauth_account.avatar_url = profile.get("picture")
        user.display_name = user.display_name or profile.get("name")
        user.avatar_url = user.avatar_url or profile.get("picture")
        return user

    user_result = await db.execute(
        select(User).where(User.email == provider_email.lower(), User.password_hash.is_not(None))
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        user = User(
            email=provider_email.lower(),
            password_hash=None,
            display_name=profile.get("name") or provider_email.split("@", 1)[0],
            avatar_url=profile.get("picture"),
        )
        db.add(user)
        await db.flush()

    oauth_account = OAuthAccount(
        user_id=user.user_id,
        provider=provider,
        provider_user_id=provider_user_id,
        provider_email=provider_email.lower(),
        provider_name=profile.get("name"),
        avatar_url=profile.get("picture"),
    )
    db.add(oauth_account)
    return user


@router.get("/oauth/google/callback")
async def google_callback(
    code: str,
    state: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> RedirectResponse:
    expected_state = request.cookies.get(settings.oauth_state_cookie_name)
    if not expected_state or not secrets.compare_digest(expected_state, state):
        raise HTTPException(status_code=401, detail="Invalid OAuth state")

    profile = await fetch_google_profile(code)
    user = await login_or_create_oauth_user(db, profile, "google")
    response = RedirectResponse(settings.frontend_origin)
    response.delete_cookie(settings.oauth_state_cookie_name, path="/")
    await create_session(db, user, request, response)
    await db.commit()
    return response


@router.get("/oauth/github/start", response_model=MessageResponse)
async def github_start() -> MessageResponse:
    return MessageResponse(message="GitHub OAuth is reserved for a later release")


@router.get("/oauth/github/callback", response_model=MessageResponse)
async def github_callback() -> MessageResponse:
    return MessageResponse(message="GitHub OAuth is reserved for a later release")
