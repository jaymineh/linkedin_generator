import { useEffect, useState } from "react";
import Head from "next/head";
import Link from "next/link";

import AppShell from "../components/AppShell";
import { HistoryItem, deleteGeneration, getHistory } from "../lib/api";
import { trackEvent, trackException } from "../lib/telemetry";

export default function History() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getHistory();
      setItems(result);
      trackEvent("frontend_history_loaded", {}, { item_count: result.length });
    } catch (error) {
      const exception = error instanceof Error ? error : new Error("History load failed");
      trackException(exception, { surface: "history_page_load" });
      setError("Could not load history.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadHistory();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await deleteGeneration(id);
      setItems((current) => current.filter((item) => item.id !== id));
      trackEvent("frontend_history_delete_succeeded");
    } catch (error) {
      const exception = error instanceof Error ? error : new Error("History delete failed");
      trackException(exception, { surface: "history_page_delete" });
      setError("Could not delete that generation.");
    }
  };

  return (
    <>
      <Head>
        <title>History | LinkedIn Post Generator</title>
      </Head>

      <AppShell active="history">
        <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
          <div className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-600 dark:text-indigo-300">
                Library
              </p>
              <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Generation history</h1>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                Revisit topics you have already turned into posts.
              </p>
            </div>
            <Link
              href="/"
              className="inline-flex items-center justify-center rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-md shadow-indigo-600/25 transition hover:bg-indigo-500"
            >
              New post
            </Link>
          </div>

          {error && (
            <div className="mb-4 rounded-xl border border-red-200/80 bg-red-50/90 px-4 py-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200">
              {error}
            </div>
          )}
          {loading && (
            <div className="flex items-center gap-3 rounded-xl border border-slate-200/80 bg-white/70 px-4 py-4 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900/60 dark:text-slate-300">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-200 border-t-indigo-600 dark:border-slate-600 dark:border-t-indigo-400" />
              Loading your generations…
            </div>
          )}
          {!loading && items.length === 0 && (
            <p className="rounded-xl border border-dashed border-slate-200/90 bg-white/50 px-4 py-8 text-center text-sm text-slate-500 dark:border-slate-600 dark:bg-slate-900/40 dark:text-slate-400">
              No posts generated yet.{" "}
              <Link href="/" className="font-semibold text-indigo-600 hover:underline dark:text-indigo-300">
                Go generate one
              </Link>
              .
            </p>
          )}

          <div className="flex flex-col gap-4">
            {items.map((item) => (
              <div
                key={item.id}
                className="rounded-2xl border border-slate-200/80 bg-white/85 p-5 shadow-md shadow-slate-900/5 dark:border-slate-700/80 dark:bg-slate-900/70 dark:shadow-none"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-slate-900 dark:text-white">{item.topic}</p>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                      {item.audience} · {item.tone} · {item.style_mode} ·{" "}
                      {new Date(item.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDelete(item.id)}
                    className="shrink-0 rounded-lg border border-red-100 px-2.5 py-1 text-xs font-semibold text-red-600 transition hover:bg-red-50 dark:border-red-900/40 dark:text-red-300 dark:hover:bg-red-950/40"
                  >
                    Delete
                  </button>
                </div>
                <p className="mt-3 text-xs leading-relaxed text-slate-600 dark:text-slate-300">{item.posts[0]?.hook}</p>
              </div>
            ))}
          </div>
        </div>
      </AppShell>
    </>
  );
}
