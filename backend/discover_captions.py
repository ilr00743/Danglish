from __future__ import annotations

import argparse
import sys
from pathlib import Path

from caption_discovery import discover_captions, write_discovery_report
from youtube_adapter import get_youtube_client


def load_env_file() -> None:
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        return

    load_dotenv()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover Danish caption availability for YouTube channel uploads."
    )
    parser.add_argument(
        "--channel-ids",
        required=True,
        help="Comma-separated list of YouTube channel IDs.",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="Report format (default: csv).",
    )
    parser.add_argument(
        "--output",
        help="Optional output file. Defaults to stdout.",
    )
    parser.add_argument(
        "--newer-first",
        action="store_true",
        help="Scan newest uploads first. Defaults to older uploads first.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of videos to inspect across all channels.",
    )
    parser.add_argument(
        "--sleep-ms",
        type=int,
        default=200,
        help="Delay in milliseconds between transcript requests (default: 200).",
    )
    return parser.parse_args()


def parse_channel_ids(value: str) -> list[str]:
    channel_ids = [part.strip() for part in value.split(",") if part.strip()]
    if not channel_ids:
        raise ValueError("Provide at least one channel ID.")
    return channel_ids


def log_progress(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def main() -> None:
    load_env_file()
    args = parse_args()
    try:
        youtube = get_youtube_client()
        rows = discover_captions(
            youtube,
            parse_channel_ids(args.channel_ids),
            older_first=not args.newer_first,
            sleep_ms=args.sleep_ms,
            limit=args.limit,
            progress=log_progress,
        )
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from None

    if args.output:
        output_path = Path(args.output)
        with output_path.open("w", encoding="utf-8", newline="") as stream:
            write_discovery_report(rows, stream, args.format)
    else:
        write_discovery_report(rows, sys.stdout, args.format)


if __name__ == "__main__":
    main()
