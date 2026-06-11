const DANISH_WORD_CHARS = "A-Za-z0-9_æøåÆØÅ";

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function buildExactWordRegex(query: string): RegExp | null {
  const cleanQuery = query.trim();
  if (!cleanQuery) {
    return null;
  }

  return new RegExp(
    `(^|[^${DANISH_WORD_CHARS}])(${escapeRegExp(cleanQuery)})(?=$|[^${DANISH_WORD_CHARS}])`,
    "gi",
  );
}
