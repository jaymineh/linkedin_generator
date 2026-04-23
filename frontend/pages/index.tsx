import { useEffect, useState } from "react";
import Head from "next/head";
import Link from "next/link";

import GeneratorForm from "../components/GeneratorForm";
import PostCard from "../components/PostCard";
import StyleImportPanel from "../components/StyleImportPanel";
import { GenerateRequest, PostVariant, StyleProfile, generatePosts, getStyleProfile } from "../lib/api";

export default function Home() {
  const [posts, setPosts] = useState<PostVariant[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [styleProfile, setStyleProfile] = useState<StyleProfile | null>(null);

  useEffect(() => {
    getStyleProfile()
      .then(setStyleProfile)
      .catch(() => setStyleProfile(null));
  }, []);

  const handleGenerate = async (req: GenerateRequest) => {
    setLoading(true);
    setError(null);
    setPosts([]);
    try {
      const result = await generatePosts(req);
      setPosts(result.posts);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>LinkedIn Post Generator</title>
      </Head>

      <div className="min-h-screen bg-gray-50">
        <nav className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
          <span className="font-semibold text-gray-900">LinkedIn Post Generator</span>
          <Link href="/history" className="text-sm text-gray-500 hover:text-gray-900">
            History
          </Link>
        </nav>

        <div className="mx-auto grid max-w-6xl grid-cols-1 gap-8 px-6 py-10 lg:grid-cols-5">
          <div className="lg:col-span-2">
            <h1 className="mb-6 text-xl font-bold text-gray-900">Generate a LinkedIn Post</h1>
            <GeneratorForm
              onGenerate={handleGenerate}
              loading={loading}
              hasStyleProfile={Boolean(styleProfile)}
            />
            <StyleImportPanel existingProfile={styleProfile} onProfileUpdated={setStyleProfile} />
          </div>

          <div className="lg:col-span-3 flex flex-col gap-4">
            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                {error}
              </div>
            )}
            {loading && (
              <div className="py-12 text-center text-sm text-gray-500">Generating your posts...</div>
            )}
            {!loading && posts.length === 0 && !error && (
              <div className="py-12 text-center text-sm text-gray-400">
                Fill in the form and click Generate to see your post here.
              </div>
            )}
            {posts.map((post, index) => (
              <PostCard key={`${post.style}-${index}`} post={post} />
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
