"use client";

import { FormEvent, useEffect, useState } from "react";

type SearchBarProps = {
  initialValue?: string;
  onSearch: (value: string) => Promise<void> | void;
  loading?: boolean;
  compact?: boolean;
};

export default function SearchBar({
  initialValue = "",
  onSearch,
  loading = false,
  compact = false,
}: SearchBarProps) {
  const [value, setValue] = useState(initialValue);

  useEffect(() => {
    setValue(initialValue);
  }, [initialValue]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onSearch(value);
  };

  return (
    <form onSubmit={handleSubmit} className={`w-full ${compact ? "max-w-3xl" : "max-w-4xl"}`}>
      <div className="panel flex items-center gap-2 p-2">
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Search Danish word..."
          className="h-12 w-full rounded-xl bg-transparent px-4 text-lg outline-none placeholder:text-muted"
          aria-label="Search Danish word"
        />
        <button
          type="submit"
          disabled={loading}
          className="h-12 min-w-32 rounded-xl bg-accent px-6 font-semibold text-white transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </div>
    </form>
  );
}
