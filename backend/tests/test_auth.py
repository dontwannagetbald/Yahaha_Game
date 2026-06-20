import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.auth as auth_module
from app.auth import login_or_create_oauth_user
from app.db import get_session as app_get_session
from app.main import app
from app.models import Base, OAuthAccount, User


@pytest_asyncio.fixture()
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest.fixture()
def client(session_factory):
    async def override_get_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[app_get_session] = override_get_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_email_register_creates_user_session_and_no_oauth(client, session_factory):
    response = client.post(
        "/api/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )

    assert response.status_code == 201
    assert response.json()["user"]["email"] == "user@example.com"
    assert "yahaha_session" in response.cookies

    async def inspect():
        async with session_factory() as session:
            users = (await session.execute(select(User))).scalars().all()
            oauth_accounts = (await session.execute(select(OAuthAccount))).scalars().all()
            assert len(users) == 1
            assert users[0].password_hash is not None
            assert "password123" not in users[0].password_hash
            assert oauth_accounts == []

    import asyncio

    asyncio.run(inspect())


def test_email_register_persists_display_name_and_avatar(client, session_factory):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "creator@example.com",
            "password": "password123",
            "display_name": "创作者小王",
            "avatar_url": "http://localhost:9000/yahaha-game/avatars/registrations/demo/avatar.png",
        },
    )

    assert response.status_code == 201
    assert response.json()["user"]["display_name"] == "创作者小王"
    assert response.json()["user"]["avatar_url"].endswith("/avatar.png")

    async def inspect():
        async with session_factory() as session:
            user = (await session.execute(select(User))).scalars().one()
            assert user.display_name == "创作者小王"
            assert user.avatar_url is not None
            assert user.avatar_url.endswith("/avatar.png")

    import asyncio

    asyncio.run(inspect())


def test_duplicate_email_register_is_rejected(client):
    payload = {"email": "user@example.com", "password": "password123"}

    first = client.post("/api/auth/register", json=payload)
    second = client.post("/api/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_email_login_and_me(client):
    client.post(
        "/api/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )
    logout = client.post("/api/auth/logout")

    login = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    me = client.get("/api/auth/me")

    assert logout.status_code == 200
    assert login.status_code == 200
    assert me.status_code == 200
    assert me.json()["user"]["email"] == "user@example.com"


def test_email_login_rejects_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )

    response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "wrong"},
    )

    assert response.status_code == 401


def test_email_register_rejects_weak_password(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "user@example.com", "password": "abcdefgh"},
    )

    assert response.status_code == 422


def test_avatar_presign_returns_unsigned_registration_contract(client):
    class StubStorageService:
        def build_registration_avatar_object_key(self, *, upload_id, filename: str) -> str:
            return f"avatars/registrations/{upload_id}/avatar.png"

        def build_presigned_upload_url(self, object_key: str, *, expires_in: int = 900):
            return type(
                "Result",
                (),
                {
                    "url": f"http://minio.local/presigned/{object_key}",
                    "expires_in": expires_in,
                },
            )()

    app.dependency_overrides[auth_module.get_storage_service] = lambda: StubStorageService()
    try:
        response = client.post(
            "/api/auth/avatar/presign",
            json={
                "filename": "avatar.png",
                "mime_type": "image/png",
                "size_bytes": 2048,
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["object_key"].startswith("avatars/registrations/")
        assert body["upload_url"].startswith("http://minio.local/presigned/")
    finally:
        app.dependency_overrides.pop(auth_module.get_storage_service, None)


def test_avatar_complete_returns_public_avatar_url(client):
    class StubStorageService:
        def build_public_read_url(self, object_key: str) -> str:
            return f"http://localhost:9000/yahaha-game/{object_key}"

    app.dependency_overrides[auth_module.get_storage_service] = lambda: StubStorageService()
    try:
        response = client.post(
            "/api/auth/avatar/complete",
            json={
                "upload_id": "11111111-1111-1111-1111-111111111111",
                "object_key": "avatars/registrations/11111111-1111-1111-1111-111111111111/avatar.png",
                "filename": "avatar.png",
                "mime_type": "image/png",
                "size_bytes": 2048,
            },
        )

        assert response.status_code == 200
        assert response.json() == {
            "avatar_url": "http://localhost:9000/yahaha-game/avatars/registrations/11111111-1111-1111-1111-111111111111/avatar.png"
        }
    finally:
        app.dependency_overrides.pop(auth_module.get_storage_service, None)


@pytest.mark.asyncio
async def test_google_oauth_first_login_creates_user_and_oauth(session_factory):
    profile = {
        "sub": "google-1",
        "email": "google@example.com",
        "email_verified": True,
        "name": "Google User",
        "picture": "https://example.com/avatar.png",
    }

    async with session_factory() as session:
        user = await login_or_create_oauth_user(session, profile, "google")
        await session.commit()

        oauth_accounts = (await session.execute(select(OAuthAccount))).scalars().all()
        users = (await session.execute(select(User))).scalars().all()

    assert user.email == "google@example.com"
    assert user.password_hash is None
    assert len(users) == 1
    assert len(oauth_accounts) == 1
    assert oauth_accounts[0].user_id == user.user_id
    assert oauth_accounts[0].provider == "google"


@pytest.mark.asyncio
async def test_google_oauth_second_login_reuses_same_user(session_factory):
    profile = {
        "sub": "google-1",
        "email": "google@example.com",
        "email_verified": True,
        "name": "Google User",
        "picture": "https://example.com/avatar.png",
    }

    async with session_factory() as session:
        first = await login_or_create_oauth_user(session, profile, "google")
        await session.commit()
        second = await login_or_create_oauth_user(session, profile, "google")
        await session.commit()

        users = (await session.execute(select(User))).scalars().all()
        oauth_accounts = (await session.execute(select(OAuthAccount))).scalars().all()

    assert first.user_id == second.user_id
    assert len(users) == 1
    assert len(oauth_accounts) == 1


@pytest.mark.asyncio
async def test_google_oauth_verified_email_binds_existing_local_user(session_factory):
    profile = {
        "sub": "google-1",
        "email": "user@example.com",
        "email_verified": True,
        "name": "Google User",
        "picture": "https://example.com/avatar.png",
    }

    async with session_factory() as session:
        local_user = User(
            email="user@example.com",
            password_hash="pbkdf2_sha256$200000$salt$digest",
            display_name="Local User",
        )
        session.add(local_user)
        await session.commit()

        oauth_user = await login_or_create_oauth_user(session, profile, "google")
        await session.commit()

        users = (await session.execute(select(User))).scalars().all()
        oauth_accounts = (await session.execute(select(OAuthAccount))).scalars().all()

    assert oauth_user.user_id == local_user.user_id
    assert len(users) == 1
    assert len(oauth_accounts) == 1
    assert oauth_accounts[0].user_id == local_user.user_id


@pytest.mark.asyncio
async def test_google_oauth_rejects_unverified_email(session_factory):
    profile = {
        "sub": "google-1",
        "email": "google@example.com",
        "email_verified": False,
    }

    async with session_factory() as session:
        with pytest.raises(Exception):
            await login_or_create_oauth_user(session, profile, "google")


def test_github_oauth_is_reserved(client):
    response = client.get("/api/auth/oauth/github/start")

    assert response.status_code == 200
    assert "reserved" in response.json()["message"]


def test_google_callback_sets_session_and_redirects_to_frontend(
    client, session_factory, monkeypatch
):
    async def fake_fetch_google_profile(code: str) -> dict:
        assert code == "google-code"
        return {
            "sub": "google-1",
            "email": "google@example.com",
            "email_verified": True,
            "name": "Google User",
            "picture": "https://example.com/avatar.png",
        }

    monkeypatch.setattr(auth_module, "fetch_google_profile", fake_fetch_google_profile)

    client.cookies.set("yahaha_oauth_state", "state-1")
    response = client.get(
        "/api/auth/oauth/google/callback",
        params={"code": "google-code", "state": "state-1"},
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert response.headers["location"] == "http://localhost:5173"
    assert "yahaha_session" in response.cookies

    async def inspect():
        async with session_factory() as session:
            users = (await session.execute(select(User))).scalars().all()
            oauth_accounts = (await session.execute(select(OAuthAccount))).scalars().all()
            assert len(users) == 1
            assert len(oauth_accounts) == 1
            assert oauth_accounts[0].user_id == users[0].user_id

    import asyncio

    asyncio.run(inspect())
