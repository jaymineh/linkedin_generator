import { useState } from "react";

import { GenerateRequest, StyleMode } from "../lib/api";

interface Props {
  onGenerate: (req: GenerateRequest) => void;
  loading: boolean;
  hasStyleProfile: boolean;
}

export default function GeneratorForm({ onGenerate, loading, hasStyleProfile }: Props) {
  const [topic, setTopic] = useState("");
  const [audience, setAudience] = useState("developers");
  const [tone, setTone] = useState("professional");
  const [styleMode, setStyleMode] = useState<StyleMode>("off");
  const [url, setUrl] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) {
      return;
    }
    onGenerate({
      topic,
      audience,
      tone,
      style_mode: hasStyleProfile ? styleMode : "off",
      url: url || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      <div>
        <label className="mb-1 block text-sm font-medium text-gray-700">
          What do you want to post about?
        </label>
        <textarea
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          rows={4}
          placeholder="e.g. Why AI engineers need to understand infrastructure"
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-gray-700">Target Audience</label>
        <select
          value={audience}
          onChange={(e) => setAudience(e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="developers">Developers</option>
          <option value="executives">Executives / Leadership</option>
          <option value="job_seekers">Job Seekers</option>
          <option value="general">General Professional</option>
        </select>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-gray-700">Tone</label>
        <select
          value={tone}
          onChange={(e) => setTone(e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="professional">Professional</option>
          <option value="casual">Casual</option>
          <option value="storytelling">Storytelling</option>
          <option value="thought_leader">Thought Leader</option>
        </select>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-gray-700">Writing Style</label>
        <select
          value={styleMode}
          onChange={(e) => setStyleMode(e.target.value as StyleMode)}
          disabled={!hasStyleProfile}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm disabled:bg-gray-100"
        >
          <option value="off">Off</option>
          <option value="faithful">Faithful to my previous style</option>
          <option value="improve">Use my style, then improve it</option>
        </select>
        {!hasStyleProfile && (
          <p className="mt-1 text-xs text-gray-400">
            Import previous posts below to unlock style-aware generation.
          </p>
        )}
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-gray-700">
          Article URL <span className="text-gray-400">(optional)</span>
        </label>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://..."
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
        />
      </div>

      <button
        type="submit"
        disabled={loading || !topic.trim()}
        className="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? "Generating..." : "Generate Post"}
      </button>
    </form>
  );
}
