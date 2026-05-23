"use client";

import { useState, useEffect, useSyncExternalStore } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { GenerationProgress } from "@/components/dashboard/GenerationProgress";
import { VideoPlayer } from "@/components/dashboard/VideoPlayer";
import { useVideoGeneration } from "@/hooks/useVideoGeneration";
import {
  getApiKey,
  addVideoToHistory,
  updateVideoInHistory,
  incrementUsage,
  getUsageToday,
  getDailyLimit,
} from "@/lib/storage";
import { AlertTriangle, Sparkles } from "lucide-react";

const STYLES = [
  "Brainrot Classic",
  "Meme Format",
  "Educational Parody",
  "Product Showcase",
  "Storytelling",
  "Satisfying Loop",
];

const DURATIONS = [5, 10, 15];
const ASPECT_RATIOS = [
  { value: "9:16", label: "9:16 Portrait", desc: "TikTok/Shorts" },
  { value: "16:9", label: "16:9 Landscape", desc: "YouTube" },
  { value: "1:1", label: "1:1 Square", desc: "Instagram" },
];

function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  return () => window.removeEventListener("storage", callback);
}

function getApiKeySnapshot() {
  return getApiKey("replicate") || "";
}

function getServerSnapshot() {
  return "";
}

export default function GeneratePage() {
  const [prompt, setPrompt] = useState("");
  const [style, setStyle] = useState(STYLES[0]);
  const [duration, setDuration] = useState(5);
  const [aspectRatio, setAspectRatio] = useState("9:16");
  const [currentVideoId, setCurrentVideoId] = useState<string | null>(null);

  const apiKeyValue = useSyncExternalStore(
    subscribe,
    getApiKeySnapshot,
    getServerSnapshot
  );
  const hasApiKey = apiKeyValue.length > 0;

  const { status, videoUrl, error, submit, reset } = useVideoGeneration();

  // Update video in history when status changes
  useEffect(() => {
    if (currentVideoId && status === "completed" && videoUrl) {
      updateVideoInHistory(currentVideoId, {
        status: "completed",
        videoUrl,
      });
    } else if (currentVideoId && status === "failed") {
      updateVideoInHistory(currentVideoId, { status: "failed" });
    }
  }, [status, videoUrl, currentVideoId]);

  const usageToday = getUsageToday();
  const dailyLimit = getDailyLimit();
  const isOverLimit = usageToday >= dailyLimit;

  const canSubmit =
    prompt.trim().length > 0 && hasApiKey && !isOverLimit && status === "idle";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    const videoId = `video-${Date.now()}`;
    setCurrentVideoId(videoId);

    addVideoToHistory({
      id: videoId,
      prompt,
      style,
      duration,
      aspectRatio,
      status: "processing",
      videoUrl: null,
      createdAt: new Date().toISOString(),
    });

    incrementUsage();
    await submit(prompt, style, duration, aspectRatio);
  };

  const handleReset = () => {
    reset();
    setPrompt("");
    setCurrentVideoId(null);
  };

  const isGenerating =
    status !== "idle" && status !== "completed" && status !== "failed";

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Generate Video</h1>
        <p className="text-secondary mt-1">
          Describe your idea and let AI do the rest.
        </p>
      </div>

      {/* API Key warning */}
      {!hasApiKey && (
        <Card className="border-yellow-500/30 bg-yellow-500/5">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-yellow-500">
                API Key Required
              </p>
              <p className="text-sm text-secondary mt-1">
                You need to set your Replicate API key in{" "}
                <Link
                  href="/dashboard/settings"
                  className="text-primary hover:underline"
                >
                  Settings
                </Link>{" "}
                before generating videos.
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Generation progress */}
      {isGenerating && (
        <Card>
          <GenerationProgress status={status} />
        </Card>
      )}

      {/* Error state */}
      {status === "failed" && error && (
        <Card className="border-red-500/30 bg-red-500/5">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-400">
                Generation Failed
              </p>
              <p className="text-sm text-secondary mt-1">{error}</p>
              <Button
                variant="secondary"
                size="sm"
                className="mt-3"
                onClick={handleReset}
              >
                Try Again
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Video result */}
      {status === "completed" && videoUrl && (
        <Card className="space-y-4">
          <h2 className="text-lg font-semibold text-foreground">
            Your Video is Ready!
          </h2>
          <VideoPlayer videoUrl={videoUrl} />
          <Button onClick={handleReset} variant="secondary">
            <Sparkles className="w-4 h-4 mr-2" />
            Generate Another
          </Button>
        </Card>
      )}

      {/* Form */}
      {!isGenerating && status !== "completed" && (
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Prompt */}
          <Card className="space-y-3">
            <label className="text-sm font-medium text-foreground">
              Prompt
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value.slice(0, 500))}
              placeholder="Describe your brainrot video... e.g., 'A cat explaining quantum physics while doing backflips in space'"
              rows={4}
              className="w-full px-4 py-3 bg-background border border-border rounded-lg text-foreground placeholder:text-secondary/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/25 resize-none"
            />
            <div className="flex justify-end">
              <span className="text-xs text-secondary">
                {prompt.length} / 500
              </span>
            </div>
          </Card>

          {/* Style */}
          <Card className="space-y-3">
            <label className="text-sm font-medium text-foreground">Style</label>
            <select
              value={style}
              onChange={(e) => setStyle(e.target.value)}
              className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/25"
            >
              {STYLES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </Card>

          {/* Duration */}
          <Card className="space-y-3">
            <label className="text-sm font-medium text-foreground">
              Duration
            </label>
            <div className="flex gap-3">
              {DURATIONS.map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setDuration(d)}
                  className={`flex-1 py-2.5 rounded-lg text-sm font-medium border transition-colors ${
                    duration === d
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border text-secondary hover:text-foreground hover:border-primary/30"
                  }`}
                >
                  {d}s
                </button>
              ))}
            </div>
          </Card>

          {/* Aspect Ratio */}
          <Card className="space-y-3">
            <label className="text-sm font-medium text-foreground">
              Aspect Ratio
            </label>
            <div className="flex flex-col sm:flex-row gap-3">
              {ASPECT_RATIOS.map((ar) => (
                <button
                  key={ar.value}
                  type="button"
                  onClick={() => setAspectRatio(ar.value)}
                  className={`flex-1 py-2.5 px-3 rounded-lg text-sm font-medium border transition-colors ${
                    aspectRatio === ar.value
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border text-secondary hover:text-foreground hover:border-primary/30"
                  }`}
                >
                  <div>{ar.label}</div>
                  <div className="text-xs opacity-60 mt-0.5">{ar.desc}</div>
                </button>
              ))}
            </div>
          </Card>

          {/* Submit */}
          <Button
            type="submit"
            size="lg"
            disabled={!canSubmit}
            className="w-full"
          >
            <Sparkles className="w-4 h-4 mr-2" />
            Generate Video
          </Button>

          {isOverLimit && (
            <p className="text-sm text-center text-yellow-500">
              You have reached your daily limit ({dailyLimit} videos). Upgrade to
              Pro for unlimited generations.
            </p>
          )}
        </form>
      )}
    </div>
  );
}
