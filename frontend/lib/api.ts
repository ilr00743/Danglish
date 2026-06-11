export type SearchResult = {
  caption_id: number;
  video_id: string;
  video_title: string;
  channel_name: string;
  text: string;
  start_time: number;
  duration: number;
  context: string;
};

export type Caption = {
  caption_id: number;
  text: string;
  start_time: number;
  duration: number;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export async function searchCaptions(query: string): Promise<SearchResult[]> {
  const url = `${API_BASE_URL}/api/search?q=${encodeURIComponent(query)}`;
  const res = await fetch(url, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });

  if (!res.ok) {
    const payload = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new Error(payload.detail || "Search request failed.");
  }

  const data = (await res.json()) as { results: SearchResult[] };
  return data.results ?? [];
}

export async function getVideoCaptions(videoId: string): Promise<Caption[]> {
  const url = `${API_BASE_URL}/api/videos/${encodeURIComponent(videoId)}/captions`;
  const res = await fetch(url, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });

  if (!res.ok) {
    const payload = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new Error(payload.detail || "Could not load captions.");
  }

  const data = (await res.json()) as { captions: Caption[] };
  return data.captions ?? [];
}
