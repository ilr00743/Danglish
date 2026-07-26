from __future__ import annotations

import logging
import os

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import get_db, initialize_schema
from transcript_repository import list_video_captions, search_captions as search_caption_rows

DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)
health_logger = logging.getLogger("uvicorn.error")


def get_cors_origins() -> list[str]:
    configured_origins = os.getenv("BACKEND_CORS_ORIGINS")
    if not configured_origins:
        return list(DEFAULT_CORS_ORIGINS)

    origins = [origin.strip() for origin in configured_origins.split(",") if origin.strip()]
    return origins or list(DEFAULT_CORS_ORIGINS)


def get_request_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",", maxsplit=1)[0].strip()

    if request.client:
        return request.client.host

    return "unknown"


def log_health_probe(endpoint: str, request: Request, status: str) -> None:
    health_logger.info(
        "health_probe endpoint=%s status=%s client_ip=%s user_agent=%r",
        endpoint,
        status,
        get_request_client_ip(request),
        request.headers.get("user-agent", ""),
    )


app = FastAPI(title="DanGlish API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    initialize_schema()


@app.get("/api/health")
def healthcheck(request: Request) -> dict[str, str]:
    log_health_probe("/api/health", request, "ok")
    return {"status": "ok"}


@app.get("/api/ready")
def readiness_check(request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1")).scalar_one()
    except SQLAlchemyError as exc:
        log_health_probe("/api/ready", request, "database_not_ready")
        raise HTTPException(status_code=503, detail="Database is not ready.") from exc

    log_health_probe("/api/ready", request, "ok")
    return {"status": "ok", "database": "ok"}


@app.get("/api/search")
def search_captions(
    q: str = Query(..., min_length=1, description="Danish search term"),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, list[dict]]:
    query_text = q.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    return {"results": search_caption_rows(db, query_text, limit)}


@app.get("/api/videos/{video_id}/captions")
def get_video_captions(
    video_id: str,
    db: Session = Depends(get_db),
) -> dict[str, list[dict]]:
    return {"captions": list_video_captions(db, video_id)}
