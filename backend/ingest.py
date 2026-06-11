from __future__ import annotations

import argparse

from dotenv import load_dotenv

from database import initialize_schema
from ingestion_pipeline import ingest_channels
from youtube_adapter import get_youtube_client

load_dotenv()


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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    initialize_schema()
    youtube = get_youtube_client()

    channel_ids = [value.strip() for value in args.channel_ids.split(",") if value.strip()]
    if not channel_ids:
        raise ValueError("Provide at least one channel ID.")

    stats = ingest_channels(youtube, channel_ids, args.sleep_ms)

    print(f"[DONE] Processed videos: {stats['processed']}, skipped: {stats['skipped']}")


if __name__ == "__main__":
    main()
