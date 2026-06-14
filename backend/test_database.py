from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from database import DEFAULT_DATABASE_URL, get_database_url


class DatabaseUrlTest(unittest.TestCase):
    def test_get_database_url_uses_default(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_database_url(), DEFAULT_DATABASE_URL)

    def test_get_database_url_normalizes_render_postgres_url(self) -> None:
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "postgres://user:pass@example.com:5432/danglish"},
            clear=True,
        ):
            self.assertEqual(
                get_database_url(),
                "postgresql+psycopg://user:pass@example.com:5432/danglish",
            )

    def test_get_database_url_normalizes_plain_postgresql_url(self) -> None:
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "postgresql://user:pass@example.com:5432/danglish"},
            clear=True,
        ):
            self.assertEqual(
                get_database_url(),
                "postgresql+psycopg://user:pass@example.com:5432/danglish",
            )

    def test_get_database_url_keeps_explicit_driver_url(self) -> None:
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "postgresql+psycopg://user:pass@example.com:5432/danglish"},
            clear=True,
        ):
            self.assertEqual(
                get_database_url(),
                "postgresql+psycopg://user:pass@example.com:5432/danglish",
            )


if __name__ == "__main__":
    unittest.main()
