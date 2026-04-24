import { useState } from "react";

import { PostVariant } from "../lib/api";

interface Props {
  post: PostVariant;
  onRetry?: () => void;
  retryDisabled?: boolean;
}

const styleLabels: Record<string, string> = {
  professional: "Professional",
  casual: "Casual",
  storytelling: "Storytelling",
  thought_leader: "Thought Leader",
};

export default function PostCard({ post, onRetry, retryDisabled }: Props) {
  const [copied, setCopied] = useState(false);

  const fullText = `${post.body}\n\n${post.hashtags.map((tag) => `#${tag.replace(/^#/, "")}`).join(" ")}`;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(fullText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-200/80 bg-white/90 p-6 shadow-lg shadow-indigo-500/5 ring-1 ring-slate-900/5 dark:border-slate-700/80 dark:bg-slate-900/80 dark:shadow-none dark:ring-white/10">
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-indigo-500 via-violet-500 to-fuchsia-500 opacity-90"
        aria-hidden
      />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-200">
          {styleLabels[post.style] ?? post.style}
        </span>
        <div className="flex flex-wrap items-center gap-2">
          {onRetry ? (
            <button
              type="button"
              onClick={onRetry}
              disabled={retryDisabled}
              className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-indigo-300 hover:text-indigo-700 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-indigo-400 dark:hover:text-indigo-200"
            >
              {retryDisabled ? "Retrying…" : "Retry"}
            </button>
          ) : null}
          <button
            type="button"
            onClick={handleCopy}
            className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-white dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
          >
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
      </div>

      <p className="mt-4 text-base font-semibold leading-snug text-slate-900 dark:text-white">{post.hook}</p>
      <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-slate-700 dark:text-slate-300">{post.body}</p>

      <div className="mt-4 flex flex-wrap gap-2 border-t border-slate-100 pt-4 dark:border-slate-700/80">
        {post.hashtags.map((tag) => (
          <span
            key={tag}
            className="rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-100"
          >
            #{tag.replace(/^#/, "")}
          </span>
        ))}
      </div>
    </div>
  );
}
