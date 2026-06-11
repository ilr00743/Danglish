"use client";

import { Caption } from "@/lib/api";
import { highlightQuery } from "@/lib/highlight";

type CurrentCaptionProps = {
  caption?: Caption;
  query: string;
};

export default function CurrentCaption({
  caption,
  query,
}: CurrentCaptionProps) {
  const text = caption?.text;

  return (
    <div className="panel px-5 py-4">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
        Current Caption
      </p>
      {text ? (
        <p
          className="text-xl font-semibold leading-relaxed md:text-2xl"
          dangerouslySetInnerHTML={{ __html: highlightQuery(text, query) }}
        />
      ) : (
        <p className="text-sm text-muted">No caption at this moment.</p>
      )}
    </div>
  );
}
