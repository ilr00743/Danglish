from __future__ import annotations

import unittest

from transcript_repository import SEARCH_CAPTIONS_SQL


class SearchCaptionsSqlTest(unittest.TestCase):
    def test_search_falls_back_to_exact_match_for_stop_words(self) -> None:
        self.assertIn("numnode(q.ts_query) = 0", SEARCH_CAPTIONS_SQL)
        self.assertIn("OR c.search_vector @@ q.ts_query", SEARCH_CAPTIONS_SQL)
        self.assertIn("c.text ~* :exact_word_pattern", SEARCH_CAPTIONS_SQL)


if __name__ == "__main__":
    unittest.main()
