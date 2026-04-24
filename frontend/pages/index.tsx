import { useCallback, useEffect, useState } from "react";
import Head from "next/head";

import AppShell from "../components/AppShell";
import GeneratorForm from "../components/GeneratorForm";
import PostCard from "../components/PostCard";
import StyleImportPanel from "../components/StyleImportPanel";
import { GenerateRequest, PostVariant, StyleProfile, generatePosts, getStyleProfile } from "../lib/api";
import { trackEvent, trackException } from "../lib/telemetry";

export default function Home() {
  const [posts, setPosts] = useState<PostVariant[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [styleProfile, setStyleProfile] = useState<StyleProfile | null>(null);
  const [lastRequest, setLastRequest] = useState<GenerateRequest | null>(null);

  useEffect(() => {
    getStyleProfile()
      .then(setStyleProfile)
      .catch(() => setStyleProfile(null));
  }, []);

  const handleGenerate = useCallback(async (req: GenerateRequest) => {
    setLastRequest(req);
    setLoading(true);
    setError(null);
    setPosts([]);

    const styleMode = req.style_mode || "off";
    const sourceType = req.url ? "url" : "manual";

    trackEvent("frontend_generate_submitted", {
      audience: req.audience,
      tone: req.tone,
      style_mode: styleMode,
      source_type: sourceType,
    });

    try {
      const result = await generatePosts(req);
      setPosts(result.posts);
      trackEvent(
        "frontend_generate_succeeded",
        {
          audience: req.audience,
          tone: req.tone,
          style_mode: styleMode,
          source_type: sourceType,
        },
        { post_count: result.posts.length }
      );
    } catch (error) {
      const exception = error instanceof Error ? error : new Error("Generation failed");
      trackException(exception, {
        audience: req.audience,
        tone: req.tone,
        style_mode: styleMode,
        source_type: sourceType,
        surface: "home_generate",
      });
      trackEvent("frontend_generate_failed", {
        audience: req.audience,
        tone: req.tone,
        style_mode: styleMode,
        source_type: sourceType,
      });
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  const handleRetry = useCallback(() => {
    if (!lastRequest) {
      return;
    }
    void handleGenerate(lastRequest);
  }, [lastRequest, handleGenerate]);

  return (
    <>
      <Head>
        <title>LinkedIn Post Generator</title>
        <meta name="description" content="Generate LinkedIn posts with optional style learning." />
      </Head>

      <AppShell active="generator">
        <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
          <div className="mb-10 max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-600 dark:text-indigo-300">
              AI-assisted writing
            </p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-4xl">
              Ship a sharp LinkedIn post in one pass
            </h1>
            <p className="mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300 sm:text-base">
              Tune audience and tone, optionally ground the post in an article URL, and layer on your own voice
              after you import samples.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-8 lg:grid-cols-5 lg:gap-10">
            <div className="lg:col-span-2">
              <div className="rounded-2xl border border-slate-200/80 bg-white/80 p-6 shadow-xl shadow-indigo-500/5 backdrop-blur-md dark:border-slate-700/80 dark:bg-slate-900/60 dark:shadow-none">
                <h2 className="mb-5 text-lg font-bold text-slate-900 dark:text-white">Composer</h2>
                <GeneratorForm
                  onGenerate={handleGenerate}
                  loading={loading}
                  hasStyleProfile={Boolean(styleProfile)}
                />
              </div>
              <StyleImportPanel existingProfile={styleProfile} onProfileUpdated={setStyleProfile} />
            </div>

            <div className="flex flex-col gap-5 lg:col-span-3">
              {error && (
                <div className="rounded-xl border border-red-200/80 bg-red-50/90 px-4 py-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200">
                  {error}
                </div>
              )}
              {loading && (
                <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-indigo-200/80 bg-white/60 py-16 text-center dark:border-indigo-500/30 dark:bg-slate-900/40">
                  <div className="h-10 w-10 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600 dark:border-slate-600 dark:border-t-indigo-400" />
                  <p className="mt-4 text-sm font-medium text-slate-600 dark:text-slate-300">Crafting your post…</p>
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">This usually takes a few seconds.</p>
                </div>
              )}
              {!loading && posts.length === 0 && !error && (
                <div className="rounded-2xl border border-dashed border-slate-200/90 bg-white/50 py-16 text-center text-sm text-slate-500 dark:border-slate-600 dark:bg-slate-900/40 dark:text-slate-400">
                  Your generated post will appear here. Fill the composer and hit{" "}
                  <span className="font-semibold text-indigo-600 dark:text-indigo-300">Generate post</span>.
                </div>
              )}
              {posts.map((post, index) => (
                <PostCard
                  key={`${post.style}-${index}-${post.hook.slice(0, 24)}`}
                  post={post}
                  onRetry={lastRequest ? handleRetry : undefined}
                  retryDisabled={loading}
                />
              ))}
            </div>
          </div>
        </div>
      </AppShell>
    </>
  );
}
