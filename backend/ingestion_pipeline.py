from __future__ import annotations

import time
from typing import Any

from googleapiclient.errors import HttpError

from database import SessionLocal
from transcript_repository import delete_video, replace_video_transcript
from youtube_adapter import (
    fetch_channel_uploads_playlist_id,
    fetch_manual_danish_transcript,
    iter_channel_videos,
)


def ingest_channels(
    youtube: Any,
    channel_ids: list[str],
    sleep_ms: int,
) -> dict[str, int]:
    processed = 0
    skipped = 0

    for channel_id in channel_ids:
        try:
            uploads_playlist_id, channel_name = fetch_channel_uploads_playlist_id(youtube, channel_id)
        except Exception as exc:
            print(f"[WARN] Skipping channel {channel_id}: {exc}")
            skipped += 1
            continue

        print(f"[INFO] Ingesting channel: {channel_name} ({channel_id})")
        for video in iter_channel_videos(youtube, uploads_playlist_id):
            video_id = video["video_id"]
            title = video["title"]
            try:
                transcript = fetch_manual_danish_transcript(video_id)
            except HttpError as exc:
                print(f"[WARN] API error for {video_id}: {exc}")
                skipped += 1
                continue

            if not transcript:
                with SessionLocal.begin() as db:
                    delete_video(db, video_id)
                print(f"[SKIP] No manually added Danish transcript for {video_id} - {title}")
                skipped += 1
                continue

            with SessionLocal.begin() as db:
                replace_video_transcript(db, video_id, title, channel_name, transcript)
            processed += 1
            print(f"[OK] Indexed {video_id} - {title}")
            time.sleep(sleep_ms / 1000)

    return {"processed": processed, "skipped": skipped}
