from __future__ import annotations

import socket
import unittest
from unittest.mock import patch

from youtube_adapter import (
    inspect_danish_transcript,
    prefer_ipv4_addresses,
    select_videos_by_date,
)


class FakeTranscript:
    def __init__(self, language_code: str, is_generated: bool) -> None:
        self.language_code = language_code
        self.is_generated = is_generated


class FakeTranscriptList:
    def __init__(self, manual: FakeTranscript | None, generated: FakeTranscript | None) -> None:
        self.manual = manual
        self.generated = generated

    def find_manually_created_transcript(self, languages: list[str]) -> FakeTranscript:
        if self.manual and self.manual.language_code in languages:
            return self.manual
        raise LookupError("manual transcript not found")

    def find_generated_transcript(self, languages: list[str]) -> FakeTranscript:
        if self.generated and self.generated.language_code in languages:
            return self.generated
        raise LookupError("generated transcript not found")


class FakeTranscriptApi:
    def __init__(self, transcript_list: FakeTranscriptList) -> None:
        self.transcript_list = transcript_list

    def list(self, video_id: str) -> FakeTranscriptList:
        return self.transcript_list


class FailingTranscriptApi:
    def list(self, video_id: str) -> FakeTranscriptList:
        raise RuntimeError("transcripts disabled")


class InspectDanishTranscriptTest(unittest.TestCase):
    def test_prefers_manual_danish_caption_availability(self) -> None:
        api = FakeTranscriptApi(
            FakeTranscriptList(
                manual=FakeTranscript("da", is_generated=False),
                generated=FakeTranscript("da", is_generated=True),
            )
        )

        inspection = inspect_danish_transcript("video-1", transcript_api=api)

        self.assertEqual(inspection.status, "manual_da")
        self.assertEqual(inspection.language_code, "da")
        self.assertFalse(inspection.is_generated)
        self.assertIsNone(inspection.error)

    def test_reports_generated_danish_caption_availability(self) -> None:
        api = FakeTranscriptApi(
            FakeTranscriptList(
                manual=None,
                generated=FakeTranscript("da", is_generated=True),
            )
        )

        inspection = inspect_danish_transcript("video-1", transcript_api=api)

        self.assertEqual(inspection.status, "generated_da")
        self.assertEqual(inspection.language_code, "da")
        self.assertTrue(inspection.is_generated)
        self.assertIsNone(inspection.error)

    def test_reports_no_danish_caption_availability(self) -> None:
        api = FakeTranscriptApi(FakeTranscriptList(manual=None, generated=None))

        inspection = inspect_danish_transcript("video-1", transcript_api=api)

        self.assertEqual(inspection.status, "no_da")
        self.assertIsNone(inspection.language_code)
        self.assertIsNone(inspection.is_generated)
        self.assertIsNone(inspection.error)

    def test_reports_lookup_failure(self) -> None:
        inspection = inspect_danish_transcript("video-1", transcript_api=FailingTranscriptApi())

        self.assertEqual(inspection.status, "lookup_failed")
        self.assertIn("transcripts disabled", inspection.error or "")


class SelectVideosByDateTest(unittest.TestCase):
    def test_filters_inclusive_date_range_and_sorts_oldest_first(self) -> None:
        videos = [
            {"video_id": "new", "title": "New", "published_at": "2026-06-01T10:00:00Z"},
            {"video_id": "middle", "title": "Middle", "published_at": "2020-05-10T12:00:00Z"},
            {"video_id": "old", "title": "Old", "published_at": "2018-01-01T10:00:00Z"},
        ]

        selected = select_videos_by_date(
            videos,
            older_first=True,
            published_from="2020-05-10",
            published_to="2026-06-01",
        )

        self.assertEqual([video["video_id"] for video in selected], ["middle", "new"])

    def test_sorts_newest_first(self) -> None:
        videos = [
            {"video_id": "old", "title": "Old", "published_at": "2018-01-01T10:00:00Z"},
            {"video_id": "new", "title": "New", "published_at": "2026-06-01T10:00:00Z"},
        ]

        selected = select_videos_by_date(videos, older_first=False)

        self.assertEqual([video["video_id"] for video in selected], ["new", "old"])

    def test_sorts_undated_videos_last_in_both_directions(self) -> None:
        videos = [
            {"video_id": "undated", "title": "Undated", "published_at": ""},
            {"video_id": "old", "title": "Old", "published_at": "2018-01-01T10:00:00Z"},
            {"video_id": "new", "title": "New", "published_at": "2026-06-01T10:00:00Z"},
        ]

        oldest_first = select_videos_by_date(videos, older_first=True)
        newest_first = select_videos_by_date(videos, older_first=False)

        self.assertEqual([video["video_id"] for video in oldest_first], ["old", "new", "undated"])
        self.assertEqual([video["video_id"] for video in newest_first], ["new", "old", "undated"])

    def test_date_filter_skips_undated_videos(self) -> None:
        videos = [
            {"video_id": "undated", "title": "Undated", "published_at": ""},
            {"video_id": "dated", "title": "Dated", "published_at": "2020-01-01T10:00:00Z"},
        ]

        selected = select_videos_by_date(videos, published_from="2020-01-01")

        self.assertEqual([video["video_id"] for video in selected], ["dated"])

    def test_rejects_reversed_date_range(self) -> None:
        with self.assertRaises(ValueError):
            select_videos_by_date([], published_from="2026-01-01", published_to="2020-01-01")


class YouTubeNetworkPreferenceTest(unittest.TestCase):
    def test_prefers_ipv4_for_youtube_hosts_when_available(self) -> None:
        ipv6 = (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("2001:4860:4802:38::223", 443, 0, 0))
        ipv4 = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("216.239.36.223", 443))

        with patch.dict("os.environ", {"YOUTUBE_FORCE_IPV4": "1"}):
            addresses = prefer_ipv4_addresses("www.googleapis.com", [ipv6, ipv4])

        self.assertEqual(addresses, [ipv4])

    def test_preserves_non_youtube_hosts(self) -> None:
        ipv6 = (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("2001:db8::1", 443, 0, 0))
        ipv4 = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.1", 443))

        addresses = prefer_ipv4_addresses("example.com", [ipv6, ipv4])

        self.assertEqual(addresses, [ipv6, ipv4])


if __name__ == "__main__":
    unittest.main()
