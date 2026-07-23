from __future__ import annotations

import unittest
from unittest.mock import Mock

from fastapi import HTTPException
from sqlalchemy.exc import OperationalError

from main import healthcheck, readiness_check


class HealthEndpointTest(unittest.TestCase):
    def test_healthcheck_returns_ok_without_database(self) -> None:
        self.assertEqual(healthcheck(), {"status": "ok"})

    def test_readiness_check_queries_database(self) -> None:
        scalar_result = Mock()
        scalar_result.scalar_one.return_value = 1
        db = Mock()
        db.execute.return_value = scalar_result

        self.assertEqual(readiness_check(db), {"status": "ok", "database": "ok"})
        db.execute.assert_called_once()
        scalar_result.scalar_one.assert_called_once_with()

    def test_readiness_check_returns_503_when_database_fails(self) -> None:
        db = Mock()
        db.execute.side_effect = OperationalError("SELECT 1", {}, Exception("offline"))

        with self.assertRaises(HTTPException) as context:
            readiness_check(db)

        self.assertEqual(context.exception.status_code, 503)
        self.assertEqual(context.exception.detail, "Database is not ready.")


if __name__ == "__main__":
    unittest.main()
