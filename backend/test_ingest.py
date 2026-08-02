from __future__ import annotations

from io import StringIO
import unittest
from unittest.mock import patch

from ingest import parse_args


class IngestCliTest(unittest.TestCase):
    def test_parses_sort_and_date_filters(self) -> None:
        with patch(
            "sys.argv",
            [
                "ingest.py",
                "--channel-ids",
                "channel-1",
                "--newer-first",
                "--published-from",
                "2020-01-01",
                "--published-to",
                "2026-12-31",
            ],
        ):
            args = parse_args()

        self.assertEqual(args.channel_ids, "channel-1")
        self.assertFalse(args.older_first)
        self.assertTrue(args.newer_first)
        self.assertEqual(args.published_from, "2020-01-01")
        self.assertEqual(args.published_to, "2026-12-31")

    def test_rejects_reversed_date_range_before_ingestion(self) -> None:
        with patch("sys.stderr", new_callable=StringIO), patch(
            "sys.argv",
            [
                "ingest.py",
                "--channel-ids",
                "channel-1",
                "--published-from",
                "2026-01-01",
                "--published-to",
                "2020-01-01",
            ],
        ):
            with self.assertRaises(SystemExit):
                parse_args()


if __name__ == "__main__":
    unittest.main()
