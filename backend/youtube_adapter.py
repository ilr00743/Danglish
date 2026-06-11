from __future__ import annotations

import os
from typing import Any, Iterable

from googleapiclient.discovery import build


def get_youtube_client() -> Any:
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing YOUTUBE_API_KEY in environment.")
    return build("youtube", "v3", developerKey=api_key)


def fetch_channel_uploads_playlist_id(youtube: Any, channel_id: str) -> tuple[str, str]:
    response = (
        youtube.channels()
        .list(part="contentDetails,snippet", id=channel_id, maxResults=1)
        .execute()
    )
    items = response.get("items", [])
    if not items:
        raise ValueError(f"Channel not found: {channel_id}")

    item = items[0]
    channel_name = item["snippet"]["title"]
    uploads_playlist_id = item["contentDetails"]["relatedPlaylists"]["uploads"]
    return uploads_playlist_id, channel_name


def iter_channel_videos(youtube: Any, uploads_playlist_id: str) -> Iterable[dict[str, str]]:
    page_token = None
    while True:
        response = (
            youtube.playlistItems()
            .list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=page_token,
            )
            .execute()
        )

        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            resource = snippet.get("resourceId", {})
            video_id = resource.get("videoId")
            title = snippet.get("title")
            if video_id and title:
                yield {"video_id": video_id, "title": title}

        page_token = response.get("nextPageToken")
        if not page_token:
            break


def normalize_transcript_entries(entries: Iterable[Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for part in entries:
        if isinstance(part, dict):
            normalized.append(part)
        else:
            normalized.append(
                {
                    "text": getattr(part, "text", ""),
                    "start": float(getattr(part, "start", 0.0)),
                    "duration": float(getattr(part, "duration", 0.0)),
                }
            )
    return normalized


def fetch_manual_danish_transcript(video_id: str) -> list[dict[str, Any]] | None:
    from youtube_transcript_api import YouTubeTranscriptApi

    api = YouTubeTranscriptApi()

    try:
        transcript_list = api.list(video_id)
        selected = transcript_list.find_manually_created_transcript(["da"])
        return normalize_transcript_entries(selected.fetch())
    except Exception:
        return None
