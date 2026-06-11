"use client";

import { useEffect, useMemo, useState } from "react";

import { Caption, SearchResult, getVideoCaptions } from "@/lib/api";

function findCurrentCaption(captions: Caption[], currentTime: number): Caption | undefined {
  return captions.find((caption) => {
    const start = caption.start_time;
    const end = caption.start_time + Math.max(caption.duration, 0.1);
    return currentTime >= start && currentTime < end;
  });
}

export function getSeekTarget(match?: SearchResult): number {
  return match ? Math.max(0, match.start_time - 5) : 0;
}

export function usePlaybackSession(match?: SearchResult) {
  const [captions, setCaptions] = useState<Caption[]>([]);
  const [currentTime, setCurrentTime] = useState(0);
  const [captionError, setCaptionError] = useState<string | null>(null);

  const seekTarget = useMemo(() => getSeekTarget(match), [match]);

  useEffect(() => {
    if (!match) {
      setCaptions([]);
      setCurrentTime(0);
      setCaptionError(null);
      return;
    }

    let cancelled = false;
    setCurrentTime(getSeekTarget(match));
    setCaptionError(null);

    getVideoCaptions(match.video_id)
      .then((loadedCaptions) => {
        if (!cancelled) {
          setCaptions(loadedCaptions);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setCaptions([]);
          setCaptionError(err instanceof Error ? err.message : "Could not load captions.");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [match]);

  return {
    captionError,
    currentCaption: findCurrentCaption(captions, currentTime),
    onTimeChange: setCurrentTime,
    playbackKey: match?.caption_id,
    seekTarget,
  };
}
