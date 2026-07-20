from __future__ import annotations

from io import StringIO
import unittest

from caption_discovery import CaptionDiscoveryRow, discover_captions, write_discovery_report
from youtube_adapter import DanishTranscriptInspection


class FakeRequest:
    def __init__(self, response: dict) -> None:
        self.response = response

    def execute(self) -> dict:
        return self.response


class FakeChannelsResource:
    def list(self, **kwargs: object) -> FakeRequest:
        return FakeRequest(
            {
                "items": [
                    {
                        "snippet": {"title": "DR Dansk"},
                        "contentDetails": {"relatedPlaylists": {"uploads": "uploads-1"}},
                    }
                ]
            }
        )


class FakePlaylistItemsResource:
    def list(self, **kwargs: object) -> FakeRequest:
        return FakeRequest(
            {
                "items": [
                    {
                        "snippet": {
                            "title": "New video",
                            "publishedAt": "2026-06-01T10:00:00Z",
                            "resourceId": {"videoId": "new-video"},
                        }
                    },
                    {
                        "snippet": {
                            "title": "Old video",
                            "publishedAt": "2018-01-01T10:00:00Z",
                            "resourceId": {"videoId": "old-video"},
                        }
                    },
                ]
            }
        )


class FakeYouTube:
    def channels(self) -> FakeChannelsResource:
        return FakeChannelsResource()

    def playlistItems(self) -> FakePlaylistItemsResource:
        return FakePlaylistItemsResource()


class CaptionDiscoveryTest(unittest.TestCase):
    def test_discovers_channel_captions_older_first(self) -> None:
        def inspect(video_id: str) -> DanishTranscriptInspection:
            status = "manual_da" if video_id == "old-video" else "generated_da"
            return DanishTranscriptInspection(status=status, language_code="da")

        rows = discover_captions(
            FakeYouTube(),
            ["channel-1"],
            inspect_transcript=inspect,
            older_first=True,
            sleep_ms=0,
        )

        self.assertEqual([row.video_id for row in rows], ["old-video", "new-video"])
        self.assertEqual(rows[0].title, "Old video")
        self.assertEqual(rows[0].channel_name, "DR Dansk")
        self.assertEqual(rows[0].published_at, "2018-01-01T10:00:00Z")
        self.assertEqual(rows[0].caption_status, "manual_da")
        self.assertEqual(rows[1].caption_status, "generated_da")

    def test_writes_csv_report(self) -> None:
        stream = StringIO()

        write_discovery_report(
            [
                CaptionDiscoveryRow(
                    video_id="video-1",
                    title="Video title",
                    channel_name="DR Dansk",
                    published_at="2018-01-01T10:00:00Z",
                    caption_status="manual_da",
                )
            ],
            stream,
            "csv",
        )

        self.assertIn("video_id,title,channel_name,published_at,caption_status,error", stream.getvalue())
        self.assertIn("video-1,Video title,DR Dansk,2018-01-01T10:00:00Z,manual_da,", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
