"use client";

import { SearchResult } from "@/lib/api";
import { highlightQuery } from "@/lib/highlight";
import { formatTimestamp } from "@/lib/time";

type TranscriptViewerProps = {
  query: string;
  result?: SearchResult;
  currentIndex: number;
  total: number;
  onPrevious: () => void;
  onNext: () => void;
};

export default function TranscriptViewer({
  query,
  result,
  currentIndex,
  total,
  onPrevious,
  onNext,
}: TranscriptViewerProps) {
  return (
    <div className="panel flex h-full min-h-[320px] flex-col p-5">
      <div className="mb-4 flex items-center justify-between gap-4 border-b border-black/10 pb-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-muted">Match</p>
          <p className="text-sm text-ink/80">
            {total > 0 ? `${currentIndex + 1} of ${total}` : "No results"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onPrevious}
            disabled={total <= 1}
            className="rounded-lg border border-black/10 px-3 py-2 text-sm font-semibold transition hover:bg-black/5 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Previous
          </button>
          <button
            type="button"
            onClick={onNext}
            disabled={total <= 1}
            className="rounded-lg border border-black/10 px-3 py-2 text-sm font-semibold transition hover:bg-black/5 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>

      {!result ? (
        <div className="flex h-full items-center justify-center text-center text-muted">
          Transcript snippets will appear here.
        </div>
      ) : (
        <div className="space-y-4 overflow-auto pr-1">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">Video</p>
            <p className="text-base font-semibold">{result.video_title}</p>
            <p className="text-sm text-muted">{result.channel_name}</p>
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">Context</p>
            <p
              className="mt-1 text-lg leading-relaxed"
              dangerouslySetInnerHTML={{ __html: highlightQuery(result.context || result.text, query) }}
            />
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">Timestamp</p>
            <p className="text-sm text-ink/80">{formatTimestamp(result.start_time)}</p>
          </div>
        </div>
      )}
    </div>
  );
}
