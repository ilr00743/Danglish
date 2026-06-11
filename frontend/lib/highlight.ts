import { buildExactWordRegex } from "@/lib/searchLanguage";

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function highlightQuery(text: string, query: string): string {
  const safeText = escapeHtml(text);
  const regex = buildExactWordRegex(query);
  if (!regex) {
    return safeText;
  }

  return safeText.replace(regex, "$1<mark>$2</mark>");
}
