import { useState } from "react";

import { GenerateRequest, ModelProviderOption, StyleMode } from "../lib/api";

// Hardcoded fallback model catalogue — shown when backend returns no providers
// (e.g. Azure secrets not yet propagated). The backend will still validate the
// model at generation time.
const FALLBACK_PROVIDERS: ModelProviderOption[] = [
  {
    provider: "openai",
    default_model: "gpt-5.4",
    models: ["gpt-5.4", "gpt-5.4-mini"],
  },
  {
    provider: "google",
    default_model: "gemini-2.5-flash",
    models: ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
  },
  {
    provider: "zai",
    default_model: "glm-4.7-flash",
    models: ["glm-4.7", "glm-4.7-flash"],
  },
];

interface Props {
  onGenerate: (req: GenerateRequest) => void;
  loading: boolean;
  hasStyleProfile: boolean;
  modelOptions: ModelProviderOption[];
}

const inputClass =
  "w-full rounded-xl border border-slate-200/90 bg-white/90 px-3.5 py-2.5 text-sm text-slate-900 shadow-inner shadow-slate-900/5 outline-none transition placeholder:text-slate-400 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/30 dark:border-slate-600 dark:bg-slate-900/70 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:border-indigo-400";

export default function GeneratorForm({ onGenerate, loading, hasStyleProfile, modelOptions }: Props) {
  const [topic, setTopic] = useState("");
  const [audience, setAudience] = useState("developers");
  const [tone, setTone] = useState("professional");
  const [styleMode, setStyleMode] = useState<StyleMode>("off");
  const [url, setUrl] = useState("");
  const [selectedModel, setSelectedModel] = useState("");

  // Use backend-provided options if available, otherwise fall back to the
  // hardcoded catalogue so the dropdown is never empty.
  const usingFallback = modelOptions.length === 0;
  const effectiveProviders = usingFallback ? FALLBACK_PROVIDERS : modelOptions;

  const modelEntries = effectiveProviders.flatMap((option) =>
    option.models.map((modelName) => ({
      provider: option.provider,
      model: modelName,
      size: /mini|flash|air/i.test(modelName) ? "small" : "large",
    }))
  );
  const selectedModelEntry = modelEntries.find((entry) => entry.model === selectedModel) ?? null;

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
      llm_provider: selectedModelEntry?.provider,
      llm_model: selectedModelEntry?.model,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      <div>
        <label className="mb-1.5 block text-sm font-semibold text-slate-800 dark:text-slate-200">
          AI model
        </label>
        <select
          aria-label="AI model"
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
          className={inputClass}
        >
          <option value="">Default (server)</option>
          {modelEntries.map((entry) => (
            <option key={`${entry.provider}-${entry.model}`} value={entry.model}>
              {entry.provider.toUpperCase()} — {entry.model} ({entry.size})
            </option>
          ))}
        </select>
        <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
          {usingFallback
            ? "Showing known models. Backend did not return live options — verify API key secrets are set in Azure."
            : "Choose a provisioned model, or keep \"Default\" to let the backend pick."}
        </p>
      </div>

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
        <select
          aria-label="Target audience"
          value={audience}
          onChange={(e) => setAudience(e.target.value)}
          className={inputClass}
        >
          <option value="developers">Developers</option>
          <option value="executives">Executives / Leadership</option>
          <option value="job_seekers">Job Seekers</option>
          <option value="general">General Professional</option>
        </select>
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-semibold text-slate-800 dark:text-slate-200">Tone</label>
        <select aria-label="Tone" value={tone} onChange={(e) => setTone(e.target.value)} className={inputClass}>
          <option value="professional">Professional</option>
          <option value="casual">Casual</option>
          <option value="storytelling">Storytelling</option>
          <option value="thought_leader">Thought Leader</option>
        </select>
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-semibold text-slate-800 dark:text-slate-200">Writing style</label>
        <select
          aria-label="Writing style mode"
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
