from __future__ import annotations


def build_exact_word_pattern(query: str) -> str:
    escaped = "".join(f"\\{char}" if char in r"\.^$|?*+()[]{}" else char for char in query)
    return rf"(^|[^[:alnum:]_æøåÆØÅ]){escaped}($|[^[:alnum:]_æøåÆØÅ])"
