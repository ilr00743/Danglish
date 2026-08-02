from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from fastapi import HTTPException
from sqlalchemy.exc import OperationalError

from main import healthcheck, readiness_check, search_captions


def make_request() -> Mock:
    request = Mock()
    request.headers = {
        "x-forwarded-for": "203.0.113.10, 10.0.0.1",
        "user-agent": "Pulsetic",
    }
    request.client = Mock(host="198.51.100.20")
    return request


class HealthEndpointTest(unittest.TestCase):
    def test_healthcheck_returns_ok_without_database(self) -> None:
        self.assertEqual(healthcheck(make_request()), {"status": "ok"})

    def test_healthcheck_logs_probe_metadata(self) -> None:
        with patch("main.health_logger.info") as info:
            healthcheck(make_request())

        info.assert_called_once_with(
            "health_probe endpoint=%s status=%s client_ip=%s user_agent=%r",
            "/api/health",
            "ok",
            "203.0.113.10",
            "Pulsetic",
        )

    def test_readiness_check_queries_database(self) -> None:
        scalar_result = Mock()
        scalar_result.scalar_one.return_value = 1
        db = Mock()
        db.execute.return_value = scalar_result

        self.assertEqual(readiness_check(make_request(), db), {"status": "ok", "database": "ok"})
        db.execute.assert_called_once()
        scalar_result.scalar_one.assert_called_once_with()

    def test_readiness_check_returns_503_when_database_fails(self) -> None:
        db = Mock()
        db.execute.side_effect = OperationalError("SELECT 1", {}, Exception("offline"))

        with self.assertRaises(HTTPException) as context:
            readiness_check(make_request(), db)

        self.assertEqual(context.exception.status_code, 503)
        self.assertEqual(context.exception.detail, "Database is not ready.")


class SearchEndpointTest(unittest.TestCase):
    def test_logs_when_search_has_no_results(self) -> None:
        with patch("main.search_caption_rows", return_value=[]), patch("main.search_logger.info") as info:
            response = search_captions(make_request(), q=" mangler ", limit=30, db=Mock())

        self.assertEqual(response, {"results": []})
        info.assert_called_once_with(
            "search_no_results query=%r limit=%s client_ip=%s user_agent=%r",
            "mangler",
            30,
            "203.0.113.10",
            "Pulsetic",
        )

    def test_does_not_log_when_search_has_results(self) -> None:
        results = [{"caption_id": 1, "text": "hej"}]

        with patch("main.search_caption_rows", return_value=results), patch("main.search_logger.info") as info:
            response = search_captions(make_request(), q="hej", limit=30, db=Mock())

        self.assertEqual(response, {"results": results})
        info.assert_not_called()


if __name__ == "__main__":
    unittest.main()
