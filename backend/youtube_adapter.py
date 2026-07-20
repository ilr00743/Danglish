from __future__ import annotations

from dataclasses import dataclass
import os
import socket
from typing import Any, Iterable, Sequence


DEFAULT_YOUTUBE_HTTP_TIMEOUT_SECONDS = 15
YOUTUBE_HOST_SUFFIXES = (
    "googleapis.com",
    "youtube.com",
    "youtubei.googleapis.com",
)
_ORIGINAL_GETADDRINFO = socket.getaddrinfo


def get_youtube_http_timeout_seconds() -> int:
    raw_timeout = os.getenv("YOUTUBE_HTTP_TIMEOUT_SECONDS", str(DEFAULT_YOUTUBE_HTTP_TIMEOUT_SECONDS))
    try:
        timeout = int(raw_timeout)
    except ValueError as exc:
        raise ValueError("YOUTUBE_HTTP_TIMEOUT_SECONDS must be an integer.") from exc

    if timeout <= 0:
        raise ValueError("YOUTUBE_HTTP_TIMEOUT_SECONDS must be greater than zero.")
    return timeout


def should_force_youtube_ipv4() -> bool:
    raw_value = os.getenv("YOUTUBE_FORCE_IPV4", "1").strip().lower()
    return raw_value not in {"0", "false", "no", "off"}


def is_youtube_host(host: object) -> bool:
    if not isinstance(host, str):
        return False
    normalized = host.rstrip(".").lower()
    return any(
        normalized == suffix or normalized.endswith(f".{suffix}")
        for suffix in YOUTUBE_HOST_SUFFIXES
    )


def prefer_ipv4_addresses(host: object, addresses: Sequence[Any]) -> list[Any]:
    address_list = list(addresses)
    if not should_force_youtube_ipv4() or not is_youtube_host(host):
        return address_list

    ipv4_addresses = [address for address in address_list if address[0] == socket.AF_INET]
    return ipv4_addresses or address_list


def install_youtube_ipv4_preference() -> None:
    if not should_force_youtube_ipv4() or socket.getaddrinfo is not _ORIGINAL_GETADDRINFO:
        return

    def getaddrinfo_ipv4_first(
        host: object,
        port: object,
        family: int = 0,
        type: int = 0,
        proto: int = 0,
        flags: int = 0,
    ) -> list[Any]:
        addresses = _ORIGINAL_GETADDRINFO(host, port, family, type, proto, flags)
        return prefer_ipv4_addresses(host, addresses)

    socket.getaddrinfo = getaddrinfo_ipv4_first


@dataclass(frozen=True)
class DanishTranscriptInspection:
    status: str
    language_code: str | None = None
    is_generated: bool | None = None
    error: str | None = None


def get_youtube_client() -> Any:
    try:
        import httplib2
        from googleapiclient.discovery import build
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing backend dependency 'google-api-python-client'. "
            "From the backend folder, activate the virtual environment and run "
            "'pip install -r requirements.txt'."
        ) from exc

    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing YOUTUBE_API_KEY in environment.")
    install_youtube_ipv4_preference()
    http = httplib2.Http(timeout=get_youtube_http_timeout_seconds())
    return build("youtube", "v3", developerKey=api_key, http=http)


def fetch_channel_uploads_playlist_id(youtube: Any, channel_id: str) -> tuple[str, str]:
    try:
        response = (
            youtube.channels()
            .list(part="contentDetails,snippet", id=channel_id, maxResults=1)
            .execute()
        )
    except (TimeoutError, socket.timeout, OSError) as exc:
        raise RuntimeError(
            "Could not connect to the YouTube Data API at www.googleapis.com. "
            "Check internet/VPN/firewall/proxy access, then retry."
        ) from exc

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
                yield {
                    "video_id": video_id,
                    "title": title,
                    "published_at": snippet.get("publishedAt", ""),
                }

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

    install_youtube_ipv4_preference()
    api = YouTubeTranscriptApi()

    try:
        transcript_list = api.list(video_id)
        selected = transcript_list.find_manually_created_transcript(["da"])
        return normalize_transcript_entries(selected.fetch())
    except Exception:
        return None


def inspect_danish_transcript(
    video_id: str,
    transcript_api: Any | None = None,
) -> DanishTranscriptInspection:
    if transcript_api is None:
        from youtube_transcript_api import YouTubeTranscriptApi

        install_youtube_ipv4_preference()
        transcript_api = YouTubeTranscriptApi()

    try:
        transcript_list = transcript_api.list(video_id)
    except Exception as exc:
        return DanishTranscriptInspection(status="lookup_failed", error=str(exc))

    try:
        manual = transcript_list.find_manually_created_transcript(["da"])
        return DanishTranscriptInspection(
            status="manual_da",
            language_code=getattr(manual, "language_code", "da"),
            is_generated=False,
        )
    except Exception:
        pass

    try:
        generated = transcript_list.find_generated_transcript(["da"])
        return DanishTranscriptInspection(
            status="generated_da",
            language_code=getattr(generated, "language_code", "da"),
            is_generated=True,
        )
    except Exception:
        pass

    return DanishTranscriptInspection(status="no_da")
