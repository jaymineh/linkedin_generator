import { useMemo, useState } from "react";

import { importStylePosts, StyleProfile } from "../lib/api";
import { trackEvent, trackException } from "../lib/telemetry";

interface Props {
  existingProfile: StyleProfile | null;
  onProfileUpdated: (profile: StyleProfile) => void;
}

const panelClass =
  "mt-8 flex flex-col gap-4 rounded-2xl border border-slate-200/80 bg-white/80 p-6 shadow-lg shadow-indigo-500/5 backdrop-blur-md dark:border-slate-700/80 dark:bg-slate-900/60 dark:shadow-none";

const textareaClass =
  "w-full rounded-xl border border-slate-200/90 bg-white/90 px-3.5 py-2.5 text-sm text-slate-900 shadow-inner outline-none transition placeholder:text-slate-400 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/30 dark:border-slate-600 dark:bg-slate-900/70 dark:text-slate-100 dark:placeholder:text-slate-500";

export default function StyleImportPanel({ existingProfile, onProfileUpdated }: Props) {
  const [rawPosts, setRawPosts] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const parsedCount = useMemo(() => {
    return rawPosts
      .split("\n---\n")
      .map((post) => post.trim())
      .filter(Boolean).length;
  }, [rawPosts]);

  const handleAnalyze = async () => {
    const posts = rawPosts
      .split("\n---\n")
      .map((post) => post.trim())
      .filter(Boolean);

    if (posts.length < 3) {
      trackEvent("frontend_style_import_validation_failed", {
        reason: "insufficient_posts",
      });
      setError("Paste at least 3 previous posts separated by ---");
      return;
    }

    setLoading(true);
    setError(null);
    trackEvent("frontend_style_import_submitted", {}, { sample_count: posts.length });
    try {
      const profile = await importStylePosts(posts);
      onProfileUpdated(profile);
      setRawPosts("");
      trackEvent("frontend_style_import_succeeded", {}, { sample_count: posts.length });
    } catch (error) {
      const exception = error instanceof Error ? error : new Error("Style import failed");
      trackException(exception, {
        surface: "style_import_panel",
      });
      trackEvent("frontend_style_import_failed", {}, { sample_count: posts.length });
      setError("Could not analyze your style. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={panelClass}>
      <div>
        <h2 className="text-base font-bold text-slate-900 dark:text-white">Learn my writing style</h2>
        <p className="mt-1 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
          Paste previous LinkedIn posts separated by <code className="rounded bg-slate-100 px-1 dark:bg-slate-800">---</code>
          . The app builds a reusable profile for faithful or improved drafts.
        </p>
      </div>

      <textarea
        value={rawPosts}
        onChange={(e) => setRawPosts(e.target.value)}
        rows={10}
        placeholder={"Post 1...\n---\nPost 2...\n---\nPost 3..."}
        className={textareaClass}
      />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">{parsedCount} posts detected</span>
        <button
          type="button"
          onClick={handleAnalyze}
          disabled={loading}
          className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-md transition hover:bg-slate-800 disabled:opacity-50 dark:bg-indigo-500 dark:hover:bg-indigo-400"
        >
          {loading ? "Analyzing…" : "Analyze style"}
        </button>
      </div>

      {error && <p className="text-xs font-medium text-red-600 dark:text-red-300">{error}</p>}

      {existingProfile && (
        <div className="border-t border-slate-100 pt-4 text-sm text-slate-700 dark:border-slate-700 dark:text-slate-200">
          <p className="font-semibold text-slate-900 dark:text-white">Current style profile</p>
          <p className="mt-2 leading-relaxed">{existingProfile.voice_summary}</p>
          <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
            Based on {existingProfile.sample_count} imported posts.
          </p>
          {existingProfile.opening_patterns.length > 0 && (
            <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
              Typical openings: {existingProfile.opening_patterns.join(", ")}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
