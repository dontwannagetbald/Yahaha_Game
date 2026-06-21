from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.auth import router as auth_router
from app.config import settings
from app.create_sessions import router as create_sessions_router
from app.db import get_session
from app.games import router as games_router
from app.jobs import router as jobs_router
from app.play_events import router as play_events_router
from app.uploads import router as uploads_router


app = FastAPI(
    title="Yahaha Game API",
    version="0.1.0",
    description="Backend API docs for auth, storage, jobs, games, and play flows.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(create_sessions_router)
app.include_router(games_router)
app.include_router(play_events_router)
app.include_router(jobs_router)
app.include_router(uploads_router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    code_by_status = {
        401: "unauthorized",
        403: "forbidden",
        409: "conflict",
        404: "not_found",
        413: "file_too_large",
        503: "service_unavailable",
    }
    code = code_by_status.get(exc.status_code, "http_error")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": message}},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
async def ready(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed",
        ) from exc
    return {"status": "ok", "database": "ok"}
