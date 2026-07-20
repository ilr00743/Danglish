from __future__ import annotations

import unittest

from youtube_adapter import inspect_danish_transcript


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


if __name__ == "__main__":
    unittest.main()
