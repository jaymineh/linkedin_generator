import { useMemo, useState } from "react";

import { importStylePosts, StyleProfile } from "../lib/api";

interface Props {
  existingProfile: StyleProfile | null;
  onProfileUpdated: (profile: StyleProfile) => void;
}

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
      setError("Paste at least 3 previous posts separated by ---");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const profile = await importStylePosts(posts);
      onProfileUpdated(profile);
      setRawPosts("");
    } catch {
      setError("Could not analyze your style. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-8 flex flex-col gap-4 rounded-xl border border-gray-200 bg-white p-5">
      <div>
        <h2 className="text-sm font-semibold text-gray-900">Learn My Writing Style</h2>
        <p className="mt-1 text-xs text-gray-500">
          Paste previous LinkedIn posts separated by <code>---</code>. The app will build a
          reusable style profile.
        </p>
      </div>

      <textarea
        value={rawPosts}
        onChange={(e) => setRawPosts(e.target.value)}
        rows={10}
        placeholder={"Post 1...\n---\nPost 2...\n---\nPost 3..."}
        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
      />

      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-400">{parsedCount} posts detected</span>
        <button
          type="button"
          onClick={handleAnalyze}
          disabled={loading}
          className="rounded-lg bg-gray-900 px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          {loading ? "Analyzing..." : "Analyze Style"}
        </button>
      </div>

      {error && <p className="text-xs text-red-500">{error}</p>}

      {existingProfile && (
        <div className="border-t border-gray-100 pt-4 text-sm text-gray-700">
          <p className="font-medium text-gray-900">Current style profile</p>
          <p className="mt-2">{existingProfile.voice_summary}</p>
          <p className="mt-3 text-xs text-gray-500">
            Based on {existingProfile.sample_count} imported posts.
          </p>
          {existingProfile.opening_patterns.length > 0 && (
            <p className="mt-2 text-xs text-gray-500">
              Typical openings: {existingProfile.opening_patterns.join(", ")}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
