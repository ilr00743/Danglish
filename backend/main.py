from __future__ import annotations

import os

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db, initialize_schema
from transcript_repository import list_video_captions, search_captions as search_caption_rows

DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)


def get_cors_origins() -> list[str]:
    configured_origins = os.getenv("BACKEND_CORS_ORIGINS")
    if not configured_origins:
        return list(DEFAULT_CORS_ORIGINS)

    origins = [origin.strip() for origin in configured_origins.split(",") if origin.strip()]
    return origins or list(DEFAULT_CORS_ORIGINS)


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
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


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
