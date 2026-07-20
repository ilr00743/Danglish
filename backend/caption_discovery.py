from __future__ import annotations

import csv
import json
import time
from dataclasses import asdict, dataclass
from typing import Any, Callable, Iterable, TextIO

from youtube_adapter import (
    DanishTranscriptInspection,
    fetch_channel_uploads_playlist_id,
    inspect_danish_transcript,
    iter_channel_videos,
)


@dataclass(frozen=True)
class CaptionDiscoveryRow:
    video_id: str
    title: str
    channel_name: str
    published_at: str
    caption_status: str
    error: str | None = None


def discover_captions(
    youtube: Any,
    channel_ids: list[str],
    inspect_transcript: Callable[[str], DanishTranscriptInspection] = inspect_danish_transcript,
    older_first: bool = True,
    sleep_ms: int = 200,
    limit: int | None = None,
    progress: Callable[[str], None] | None = None,
) -> list[CaptionDiscoveryRow]:
    rows: list[CaptionDiscoveryRow] = []

    for channel_id in channel_ids:
        if progress:
            progress(f"[INFO] Loading channel {channel_id}")
        uploads_playlist_id, channel_name = fetch_channel_uploads_playlist_id(youtube, channel_id)
        if progress:
            progress(f"[INFO] Listing uploads for {channel_name} ({channel_id})")
        videos = list(iter_channel_videos(youtube, uploads_playlist_id))
        videos.sort(key=lambda video: video.get("published_at", ""), reverse=not older_first)
        if progress:
            order = "oldest first" if older_first else "newest first"
            progress(f"[INFO] Found {len(videos)} uploads for {channel_name}; scanning {order}")

        for index, video in enumerate(videos, start=1):
            if limit is not None and len(rows) >= limit:
                if progress:
                    progress(f"[DONE] Reached limit of {limit} videos")
                return rows

            video_id = video["video_id"]
            if progress:
                progress(f"[INFO] [{index}/{len(videos)}] Inspecting {video_id} - {video['title']}")
            try:
                inspection = inspect_transcript(video_id)
            except Exception as exc:
                inspection = DanishTranscriptInspection(
                    status="lookup_failed",
                    error=str(exc),
                )

            rows.append(
                CaptionDiscoveryRow(
                    video_id=video_id,
                    title=video["title"],
                    channel_name=channel_name,
                    published_at=video.get("published_at", ""),
                    caption_status=inspection.status,
                    error=inspection.error,
                )
            )
            if progress:
                progress(f"[{inspection.status}] {video_id} - {video['title']}")
            time.sleep(sleep_ms / 1000)

    if progress:
        progress(f"[DONE] Inspected {len(rows)} videos")
    return rows


def discovery_rows_as_dicts(rows: Iterable[CaptionDiscoveryRow]) -> list[dict[str, str | None]]:
    return [asdict(row) for row in rows]


def write_discovery_report(
    rows: Iterable[CaptionDiscoveryRow],
    stream: TextIO,
    report_format: str,
) -> None:
    row_dicts = discovery_rows_as_dicts(rows)
    if report_format == "json":
        json.dump(row_dicts, stream, indent=2)
        stream.write("\n")
        return

    if report_format != "csv":
        raise ValueError("report_format must be 'csv' or 'json'.")

    fieldnames = [
        "video_id",
        "title",
        "channel_name",
        "published_at",
        "caption_status",
        "error",
    ]
    writer = csv.DictWriter(stream, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(row_dicts)
