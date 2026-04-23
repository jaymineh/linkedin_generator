import { useState } from "react";

import { PostVariant } from "../lib/api";

interface Props {
  post: PostVariant;
}

const styleLabels: Record<string, string> = {
  professional: "Professional",
  casual: "Casual",
  storytelling: "Storytelling",
  thought_leader: "Thought Leader",
};

export default function PostCard({ post }: Props) {
  const [copied, setCopied] = useState(false);

  const fullText = `${post.body}\n\n${post.hashtags.map((tag) => `#${tag.replace(/^#/, "")}`).join(" ")}`;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(fullText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-gray-200 bg-white p-5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-blue-600">
          {styleLabels[post.style] ?? post.style}
        </span>
        <button
          onClick={handleCopy}
          className="rounded border border-gray-200 px-2 py-1 text-xs text-gray-500 transition-colors hover:text-gray-800"
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>

      <p className="text-sm font-semibold leading-snug text-gray-900">{post.hook}</p>
      <p className="whitespace-pre-wrap text-sm leading-relaxed text-gray-700">{post.body}</p>

      <div className="flex flex-wrap gap-1 pt-1">
        {post.hashtags.map((tag) => (
          <span key={tag} className="text-xs text-blue-500">
            #{tag.replace(/^#/, "")}
          </span>
        ))}
      </div>
    </div>
  );
}
