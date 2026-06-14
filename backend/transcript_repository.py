from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from search_language import build_exact_word_pattern

SEARCH_CAPTIONS_SQL = """
WITH q AS (
    SELECT plainto_tsquery('danish', :query) AS ts_query
)
SELECT
    c.id AS caption_id,
    v.id AS video_id,
    v.title AS video_title,
    v.channel_name,
    c.text,
    c.start_time,
    c.duration,
    CASE
        WHEN strpos(lower(c.text), lower(:query)) > 0 THEN
            trim(
                substring(
                    c.text FROM GREATEST(1, strpos(lower(c.text), lower(:query)) - 35)
                    FOR char_length(:query) + 90
                )
            )
        ELSE c.text
    END AS context,
    ts_rank(c.search_vector, q.ts_query) AS rank
FROM captions c
JOIN videos v ON v.id = c.video_id
CROSS JOIN q
WHERE c.text ~* :exact_word_pattern
    AND (
        numnode(q.ts_query) = 0
        OR c.search_vector @@ q.ts_query
    )
ORDER BY rank DESC, c.start_time ASC
LIMIT :limit;
"""


def search_captions(db: Session, query: str, limit: int) -> list[dict[str, Any]]:
    sql = text(SEARCH_CAPTIONS_SQL)

    rows = db.execute(
        sql,
        {
            "query": query,
            "exact_word_pattern": build_exact_word_pattern(query),
            "limit": limit,
        },
    ).mappings().all()
    return [
        {
            "caption_id": row["caption_id"],
            "video_id": row["video_id"],
            "video_title": row["video_title"],
            "channel_name": row["channel_name"],
            "text": row["text"],
            "start_time": row["start_time"],
            "duration": row["duration"],
            "context": row["context"],
        }
        for row in rows
    ]


def list_video_captions(db: Session, video_id: str) -> list[dict[str, Any]]:
    sql = text(
        """
        SELECT
            id AS caption_id,
            text,
            start_time,
            duration
        FROM captions
        WHERE video_id = :video_id
        ORDER BY start_time ASC, id ASC;
        """
    )

    rows = db.execute(sql, {"video_id": video_id}).mappings().all()
    return [
        {
            "caption_id": row["caption_id"],
            "text": row["text"],
            "start_time": row["start_time"],
            "duration": row["duration"],
        }
        for row in rows
    ]


def replace_video_transcript(
    db: Session,
    video_id: str,
    title: str,
    channel_name: str,
    captions: list[dict[str, Any]],
) -> None:
    db.execute(
        text(
            """
            INSERT INTO videos (id, title, channel_name)
            VALUES (:id, :title, :channel_name)
            ON CONFLICT (id)
            DO UPDATE SET
                title = EXCLUDED.title,
                channel_name = EXCLUDED.channel_name;
            """
        ),
        {"id": video_id, "title": title, "channel_name": channel_name},
    )

    db.execute(text("DELETE FROM captions WHERE video_id = :video_id"), {"video_id": video_id})

    db.execute(
        text(
            """
            INSERT INTO captions (video_id, text, start_time, duration)
            VALUES (:video_id, :text, :start_time, :duration);
            """
        ),
        [
            {
                "video_id": video_id,
                "text": entry.get("text", "").strip(),
                "start_time": float(entry.get("start", 0.0)),
                "duration": float(entry.get("duration", 0.0)),
            }
            for entry in captions
            if entry.get("text")
        ],
    )


def delete_video(db: Session, video_id: str) -> None:
    db.execute(text("DELETE FROM videos WHERE id = :video_id"), {"video_id": video_id})
