"use client";

import { useEffect, useRef, useState } from "react";

type YouTubePlayerInstance = {
  getVideoData: () => { video_id?: string };
  getCurrentTime: () => number;
  loadVideoById: (args: { videoId: string; startSeconds: number }) => void;
  seekTo: (seconds: number, allowSeekAhead?: boolean) => void;
  playVideo: () => void;
  destroy: () => void;
};

type YouTubeGlobal = {
  Player: new (
    elementId: string,
    config: {
      height: string;
      width: string;
      playerVars?: Record<string, number>;
      events?: {
        onReady?: (event?: unknown) => void;
      };
    },
  ) => YouTubePlayerInstance;
};

declare global {
  interface Window {
    YT?: YouTubeGlobal;
    onYouTubeIframeAPIReady?: () => void;
  }
}

type VideoPlayerProps = {
  videoId?: string;
  seekTarget?: number;
  playbackKey?: number | string;
  onTimeChange?: (time: number) => void;
};

const PLAYER_ELEMENT_ID = "danglish-youtube-player";

export default function VideoPlayer({
  videoId,
  seekTarget = 0,
  playbackKey,
  onTimeChange,
}: VideoPlayerProps) {
  const playerRef = useRef<YouTubePlayerInstance | null>(null);
  const playerHostRef = useRef<HTMLDivElement | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const ensurePlayer = () => {
      if (!window.YT?.Player || !playerHostRef.current || playerRef.current) {
        return;
      }

      const mountNode = document.createElement("div");
      mountNode.id = PLAYER_ELEMENT_ID;
      mountNode.className = "h-full w-full";
      playerHostRef.current.replaceChildren(mountNode);

      playerRef.current = new window.YT.Player(PLAYER_ELEMENT_ID, {
        height: "100%",
        width: "100%",
        playerVars: {
          rel: 0,
          modestbranding: 1,
        },
        events: {
          onReady: () => {
            setReady(true);
          },
        },
      });
    };

    if (window.YT?.Player) {
      ensurePlayer();
      return;
    }

    const existingScript = document.getElementById("youtube-iframe-api");
    if (!existingScript) {
      const script = document.createElement("script");
      script.id = "youtube-iframe-api";
      script.src = "https://www.youtube.com/iframe_api";
      script.async = true;
      document.body.appendChild(script);
    }

    window.onYouTubeIframeAPIReady = () => {
      ensurePlayer();
    };

    return () => {
      playerRef.current?.destroy();
      playerRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!videoId || !playerRef.current || !ready) {
      return;
    }

    const currentVideoId = playerRef.current.getVideoData().video_id;
    if (currentVideoId !== videoId) {
      playerRef.current.loadVideoById({
        videoId,
        startSeconds: seekTarget,
      });
      onTimeChange?.(seekTarget);
      return;
    }

    playerRef.current.seekTo(seekTarget, true);
    playerRef.current.playVideo();
    onTimeChange?.(seekTarget);
  }, [videoId, seekTarget, playbackKey, ready, onTimeChange]);

  useEffect(() => {
    if (!videoId || !playerRef.current || !ready || !onTimeChange) {
      return;
    }

    const timer = window.setInterval(() => {
      onTimeChange(playerRef.current?.getCurrentTime() ?? 0);
    }, 250);

    return () => {
      window.clearInterval(timer);
    };
  }, [videoId, ready, onTimeChange]);

  return (
    <div className="panel relative h-full w-full overflow-hidden">
      {!videoId ? (
        <div className="absolute inset-0 z-10 flex h-full min-h-[280px] items-center justify-center bg-panel px-8 text-center text-muted">
          Search a Danish word to load a matching YouTube segment.
        </div>
      ) : null}
      <div ref={playerHostRef} className="h-full min-h-[320px] w-full" />
    </div>
  );
}
