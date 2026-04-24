import { useEffect, useState } from "react";
import Head from "next/head";
import Link from "next/link";

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

      <div className="min-h-screen bg-gray-50">
        <nav className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
          <Link href="/" className="font-semibold text-gray-900">
            LinkedIn Post Generator
          </Link>
          <span className="text-sm text-gray-500">History</span>
        </nav>

        <div className="mx-auto max-w-4xl px-6 py-10">
          <h1 className="mb-6 text-xl font-bold text-gray-900">Generation History</h1>

          {error && (
            <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              {error}
            </div>
          )}
          {loading && <p className="text-sm text-gray-400">Loading...</p>}
          {!loading && items.length === 0 && (
            <p className="text-sm text-gray-400">No posts generated yet.</p>
          )}

          <div className="flex flex-col gap-4">
            {items.map((item) => (
              <div key={item.id} className="rounded-xl border border-gray-200 bg-white p-5">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{item.topic}</p>
                    <p className="mt-1 text-xs text-gray-400">
                      {item.audience} · {item.tone} · {item.style_mode} ·{" "}
                      {new Date(item.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="text-xs text-red-400 hover:text-red-600"
                  >
                    Delete
                  </button>
                </div>
                <p className="mt-3 text-xs text-gray-500">{item.posts[0]?.hook}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
