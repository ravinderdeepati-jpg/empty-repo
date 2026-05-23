export interface VideoHistoryItem {
  id: string;
  prompt: string;
  style: string;
  duration: number;
  aspectRatio: string;
  status: "completed" | "processing" | "failed";
  videoUrl: string | null;
  createdAt: string;
}

interface UsageData {
  date: string;
  count: number;
}

const KEYS = {
  replicateApiKey: "brainfog_replicate_api_key",
  huggingfaceApiKey: "brainfog_huggingface_api_key",
  videoHistory: "brainfog_video_history",
  usage: "brainfog_usage",
} as const;

export function getApiKey(
  provider: "replicate" | "huggingface"
): string | null {
  if (typeof window === "undefined") return null;
  const key =
    provider === "replicate"
      ? KEYS.replicateApiKey
      : KEYS.huggingfaceApiKey;
  return localStorage.getItem(key);
}

export function setApiKey(
  provider: "replicate" | "huggingface",
  key: string
): void {
  if (typeof window === "undefined") return;
  const storageKey =
    provider === "replicate"
      ? KEYS.replicateApiKey
      : KEYS.huggingfaceApiKey;
  localStorage.setItem(storageKey, key);
}

export function getVideoHistory(): VideoHistoryItem[] {
  if (typeof window === "undefined") return [];
  const data = localStorage.getItem(KEYS.videoHistory);
  if (!data) return [];
  try {
    return JSON.parse(data) as VideoHistoryItem[];
  } catch {
    return [];
  }
}

export function addVideoToHistory(item: VideoHistoryItem): void {
  if (typeof window === "undefined") return;
  const history = getVideoHistory();
  history.unshift(item);
  localStorage.setItem(KEYS.videoHistory, JSON.stringify(history));
}

export function updateVideoInHistory(
  id: string,
  updates: Partial<VideoHistoryItem>
): void {
  if (typeof window === "undefined") return;
  const history = getVideoHistory();
  const index = history.findIndex((item) => item.id === id);
  if (index !== -1) {
    history[index] = { ...history[index], ...updates };
    localStorage.setItem(KEYS.videoHistory, JSON.stringify(history));
  }
}

function getTodayString(): string {
  return new Date().toISOString().split("T")[0];
}

export function getUsageToday(): number {
  if (typeof window === "undefined") return 0;
  const data = localStorage.getItem(KEYS.usage);
  if (!data) return 0;
  try {
    const usage: UsageData = JSON.parse(data);
    if (usage.date !== getTodayString()) {
      return 0;
    }
    return usage.count;
  } catch {
    return 0;
  }
}

export function incrementUsage(): void {
  if (typeof window === "undefined") return;
  const today = getTodayString();
  const data = localStorage.getItem(KEYS.usage);
  let usage: UsageData = { date: today, count: 0 };
  if (data) {
    try {
      const parsed: UsageData = JSON.parse(data);
      if (parsed.date === today) {
        usage = parsed;
      }
    } catch {
      // Reset on parse error
    }
  }
  usage.count += 1;
  localStorage.setItem(KEYS.usage, JSON.stringify(usage));
}

export function getDailyLimit(): number {
  return 3;
}
