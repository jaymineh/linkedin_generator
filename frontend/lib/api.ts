const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type StyleMode = "off" | "faithful" | "improve";

export interface PostVariant {
  style: string;
  hook: string;
  body: string;
  hashtags: string[];
}

export interface GenerateRequest {
  topic: string;
  audience: string;
  tone: string;
  style_mode?: StyleMode;
  url?: string;
}

export interface GenerateResponse {
  generation_id: string;
  posts: PostVariant[];
}

export interface HistoryItem {
  id: string;
  topic: string;
  audience: string;
  tone: string;
  style_mode: StyleMode;
  created_at: string;
  posts: PostVariant[];
}

export interface StyleProfile {
  voice_summary: string;
  opening_patterns: string[];
  sentence_length_preference: string;
  emoji_usage: string;
  hashtag_style: string;
  cta_style: string;
  preferred_topics: string[];
  phrases_to_mimic: string[];
  phrases_to_avoid: string[];
  sample_count: number;
  created_at?: string;
}

export async function generatePosts(req: GenerateRequest): Promise<GenerateResponse> {
  const res = await fetch(`${API_BASE}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    throw new Error("Generation failed");
  }
  return res.json();
}

export async function getHistory(page = 1): Promise<HistoryItem[]> {
  const res = await fetch(`${API_BASE}/api/history?page=${page}&page_size=20`);
  if (!res.ok) {
    throw new Error("Failed to load history");
  }
  return res.json();
}

export async function deleteGeneration(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/history/${id}`, { method: "DELETE" });
  if (!res.ok) {
    throw new Error("Delete failed");
  }
}

export async function importStylePosts(posts: string[]): Promise<StyleProfile> {
  const res = await fetch(`${API_BASE}/api/style/import`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ posts }),
  });
  if (!res.ok) {
    throw new Error("Style import failed");
  }
  return res.json();
}

export async function getStyleProfile(): Promise<StyleProfile | null> {
  const res = await fetch(`${API_BASE}/api/style/profile`);
  if (res.status === 404) {
    return null;
  }
  if (!res.ok) {
    throw new Error("Failed to load style profile");
  }
  return res.json();
}
