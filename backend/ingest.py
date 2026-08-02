from __future__ import annotations

import argparse
from pathlib import Path

from database import initialize_schema
from ingestion_pipeline import ingest_channels
from youtube_adapter import get_youtube_client, select_videos_by_date


def load_env_file() -> None:
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        return

    load_dotenv(Path(__file__).resolve().parent / ".env")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest Danish YouTube transcripts into PostgreSQL."
    )
    parser.add_argument(
        "--channel-ids",
        required=True,
        help="Comma-separated list of YouTube channel IDs.",
    )
    parser.add_argument(
        "--sleep-ms",
        type=int,
        default=200,
        help="Delay in milliseconds between transcript requests (default: 200).",
    )
    order_group = parser.add_mutually_exclusive_group()
    order_group.add_argument(
        "--older-first",
        action="store_true",
        help="Ingest selected uploads from oldest to newest.",
    )
    order_group.add_argument(
        "--newer-first",
        action="store_true",
        help="Ingest selected uploads from newest to oldest.",
    )
    parser.add_argument(
        "--published-from",
        help="Only ingest videos published on or after this date (YYYY-MM-DD or ISO datetime).",
    )
    parser.add_argument(
        "--published-to",
        help="Only ingest videos published on or before this date (YYYY-MM-DD or ISO datetime).",
    )
    args = parser.parse_args()
    try:
        select_videos_by_date(
            [],
            published_from=args.published_from,
            published_to=args.published_to,
        )
    except ValueError as exc:
        parser.error(str(exc))
    return args


def parse_channel_ids(value: str) -> list[str]:
    channel_ids = [part.strip() for part in value.split(",") if part.strip()]
    if not channel_ids:
        raise ValueError("Provide at least one channel ID.")
    return channel_ids


def log(message: str) -> None:
    print(message, flush=True)


def main() -> None:
    load_env_file()
    args = parse_args()
    channel_ids = parse_channel_ids(args.channel_ids)

    log("[INFO] Initializing database schema...")
    initialize_schema()
    log("[INFO] Database schema ready.")

    log("[INFO] Creating YouTube client...")
    youtube = get_youtube_client()
    log("[INFO] YouTube client ready.")

    older_first = True if args.older_first else False if args.newer_first else None
    stats = ingest_channels(
        youtube,
        channel_ids,
        args.sleep_ms,
        older_first=older_first,
        published_from=args.published_from,
        published_to=args.published_to,
    )

    log(f"[DONE] Processed videos: {stats['processed']}, skipped: {stats['skipped']}")


if __name__ == "__main__":
    main()
