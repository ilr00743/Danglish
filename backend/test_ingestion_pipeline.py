from __future__ import annotations

import unittest
from unittest.mock import patch

from ingestion_pipeline import ingest_channels


class FakeSessionBegin:
    def __enter__(self) -> str:
        return "db"

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None


class IngestChannelsDateSelectionTest(unittest.TestCase):
    def test_ingests_selected_videos_oldest_first(self) -> None:
        uploads = [
            {"video_id": "new", "title": "New", "published_at": "2026-06-01T10:00:00Z"},
            {"video_id": "middle", "title": "Middle", "published_at": "2020-05-10T12:00:00Z"},
            {"video_id": "old", "title": "Old", "published_at": "2018-01-01T10:00:00Z"},
        ]
        indexed: list[str] = []

        def replace_transcript(db: str, video_id: str, title: str, channel_name: str, transcript: list[dict]) -> None:
            indexed.append(video_id)

        with patch("ingestion_pipeline.fetch_channel_uploads_playlist_id", return_value=("uploads", "Channel")), \
            patch("ingestion_pipeline.iter_channel_videos", return_value=uploads), \
            patch("ingestion_pipeline.fetch_manual_danish_transcript", return_value=[{"text": "hej"}]), \
            patch("ingestion_pipeline.replace_video_transcript", side_effect=replace_transcript), \
            patch("ingestion_pipeline.SessionLocal.begin", return_value=FakeSessionBegin()), \
            patch("ingestion_pipeline.time.sleep"):
            stats = ingest_channels(
                youtube=object(),
                channel_ids=["channel-1"],
                sleep_ms=0,
                older_first=True,
                published_from="2020-01-01",
                published_to="2026-12-31",
            )

        self.assertEqual(stats, {"processed": 2, "skipped": 0})
        self.assertEqual(indexed, ["middle", "new"])

    def test_ingests_selected_videos_newest_first(self) -> None:
        uploads = [
            {"video_id": "old", "title": "Old", "published_at": "2018-01-01T10:00:00Z"},
            {"video_id": "new", "title": "New", "published_at": "2026-06-01T10:00:00Z"},
        ]
        indexed: list[str] = []

        def replace_transcript(db: str, video_id: str, title: str, channel_name: str, transcript: list[dict]) -> None:
            indexed.append(video_id)

        with patch("ingestion_pipeline.fetch_channel_uploads_playlist_id", return_value=("uploads", "Channel")), \
            patch("ingestion_pipeline.iter_channel_videos", return_value=uploads), \
            patch("ingestion_pipeline.fetch_manual_danish_transcript", return_value=[{"text": "hej"}]), \
            patch("ingestion_pipeline.replace_video_transcript", side_effect=replace_transcript), \
            patch("ingestion_pipeline.SessionLocal.begin", return_value=FakeSessionBegin()), \
            patch("ingestion_pipeline.time.sleep"):
            stats = ingest_channels(
                youtube=object(),
                channel_ids=["channel-1"],
                sleep_ms=0,
                older_first=False,
                published_from="2018-01-01",
                published_to="2026-12-31",
            )

        self.assertEqual(stats, {"processed": 2, "skipped": 0})
        self.assertEqual(indexed, ["new", "old"])


if __name__ == "__main__":
    unittest.main()

