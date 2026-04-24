import { useState } from "react";

import { GenerateRequest, StyleMode } from "../lib/api";

interface Props {
  onGenerate: (req: GenerateRequest) => void;
  loading: boolean;
  hasStyleProfile: boolean;
}

const inputClass =
  "w-full rounded-xl border border-slate-200/90 bg-white/90 px-3.5 py-2.5 text-sm text-slate-900 shadow-inner shadow-slate-900/5 outline-none transition placeholder:text-slate-400 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/30 dark:border-slate-600 dark:bg-slate-900/70 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:border-indigo-400";

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
        <label className="mb-1.5 block text-sm font-semibold text-slate-800 dark:text-slate-200">
          What do you want to post about?
        </label>
        <textarea
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          rows={4}
          placeholder="e.g. Why AI engineers need to understand infrastructure"
          className={inputClass}
          required
        />
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-semibold text-slate-800 dark:text-slate-200">Target audience</label>
        <select value={audience} onChange={(e) => setAudience(e.target.value)} className={inputClass}>
          <option value="developers">Developers</option>
          <option value="executives">Executives / Leadership</option>
          <option value="job_seekers">Job Seekers</option>
          <option value="general">General Professional</option>
        </select>
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-semibold text-slate-800 dark:text-slate-200">Tone</label>
        <select value={tone} onChange={(e) => setTone(e.target.value)} className={inputClass}>
          <option value="professional">Professional</option>
          <option value="casual">Casual</option>
          <option value="storytelling">Storytelling</option>
          <option value="thought_leader">Thought Leader</option>
        </select>
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-semibold text-slate-800 dark:text-slate-200">Writing style</label>
        <select
          value={styleMode}
          onChange={(e) => setStyleMode(e.target.value as StyleMode)}
          disabled={!hasStyleProfile}
          className={`${inputClass} disabled:cursor-not-allowed disabled:opacity-60`}
        >
          <option value="off">Off</option>
          <option value="faithful">Faithful to my previous style</option>
          <option value="improve">Use my style, then improve it</option>
        </select>
        {!hasStyleProfile && (
          <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
            Import previous posts below to unlock style-aware generation.
          </p>
        )}
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-semibold text-slate-800 dark:text-slate-200">
          Article URL <span className="font-normal text-slate-400">(optional)</span>
        </label>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://..."
          className={inputClass}
        />
      </div>

      <button
        type="submit"
        disabled={loading || !topic.trim()}
        className="rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 transition hover:from-indigo-500 hover:to-violet-500 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? "Generating…" : "Generate post"}
      </button>
    </form>
  );
}
