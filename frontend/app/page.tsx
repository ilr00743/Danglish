"use client";

import { useMemo, useState } from "react";

import CurrentCaption from "@/components/CurrentCaption";
import SearchBar from "@/components/SearchBar";
import TranscriptViewer from "@/components/TranscriptViewer";
import VideoPlayer from "@/components/VideoPlayer";
import { SearchResult, searchCaptions } from "@/lib/api";
import { usePlaybackSession } from "@/lib/playbackSession";

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [hasSearched, setHasSearched] = useState(false);

  const activeResult = useMemo(() => results[currentIndex], [results, currentIndex]);
  const playbackSession = usePlaybackSession(activeResult);
  const displayError = error ?? playbackSession.captionError;

  const handleSearch = async (value: string) => {
    const cleanQuery = value.trim();
    if (!cleanQuery) {
      setError("Please enter a Danish word to search.");
      setResults([]);
      setHasSearched(false);
      return;
    }

    setLoading(true);
    setError(null);
    setQuery(cleanQuery);
    setHasSearched(true);

    try {
      const data = await searchCaptions(cleanQuery);
      setResults(data);
      setCurrentIndex(0);
      if (data.length === 0) {
        setError("No matches found in indexed transcripts.");
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Something went wrong.";
      setResults([]);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const showSplitView = hasSearched;

  if (!showSplitView) {
    return (
      <main className="flex min-h-screen items-center justify-center px-4">
        <section className="w-full max-w-4xl text-center">
          <p className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-accent">DanGlish</p>
          <h1 className="mb-8 text-4xl font-extrabold tracking-tight md:text-6xl">
            Search Danish Words In YouTube Speech
          </h1>
          <SearchBar onSearch={handleSearch} loading={loading} initialValue={query} />
          {error ? <p className="mt-4 text-sm text-red-700">{error}</p> : null}
        </section>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-[1400px] flex-col gap-4 px-4 py-6">
      <header className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-accent">DanGlish</p>
          <h1 className="text-2xl font-bold md:text-3xl">Danish Transcript Explorer</h1>
        </div>
        <SearchBar onSearch={handleSearch} loading={loading} compact initialValue={query} />
      </header>

      {displayError ? <p className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{displayError}</p> : null}

      <section className="grid flex-1 grid-cols-1 gap-4 lg:grid-cols-[2fr,1fr]">
        <div className="flex min-h-0 flex-col gap-4">
          <VideoPlayer
            videoId={activeResult?.video_id}
            seekTarget={playbackSession.seekTarget}
            playbackKey={playbackSession.playbackKey}
            onTimeChange={playbackSession.onTimeChange}
          />
          <CurrentCaption
            caption={playbackSession.currentCaption}
            query={query}
          />
        </div>
        <TranscriptViewer
          query={query}
          result={activeResult}
          currentIndex={currentIndex}
          total={results.length}
          onPrevious={() =>
            setCurrentIndex((prev) => (results.length ? (prev - 1 + results.length) % results.length : 0))
          }
          onNext={() => setCurrentIndex((prev) => (results.length ? (prev + 1) % results.length : 0))}
        />
      </section>
    </main>
  );
}
