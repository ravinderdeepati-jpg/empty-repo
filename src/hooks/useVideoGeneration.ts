"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { getApiKey } from "@/lib/storage";

export type GenerationStatus =
  | "idle"
  | "submitting"
  | "queued"
  | "processing"
  | "rendering"
  | "completed"
  | "failed";

interface UseVideoGenerationReturn {
  status: GenerationStatus;
  progress: number;
  videoUrl: string | null;
  error: string | null;
  submit: (
    prompt: string,
    style: string,
    duration: number,
    aspectRatio: string
  ) => Promise<void>;
  reset: () => void;
}

function mapApiStatus(apiStatus: string): GenerationStatus {
  switch (apiStatus) {
    case "starting":
      return "queued";
    case "processing":
      return "processing";
    case "succeeded":
      return "completed";
    case "failed":
    case "canceled":
      return "failed";
    default:
      return "processing";
  }
}

function getProgress(status: GenerationStatus): number {
  switch (status) {
    case "idle":
      return 0;
    case "submitting":
      return 10;
    case "queued":
      return 25;
    case "processing":
      return 50;
    case "rendering":
      return 75;
    case "completed":
      return 100;
    case "failed":
      return 0;
    default:
      return 0;
  }
}

export function useVideoGeneration(): UseVideoGenerationReturn {
  const [status, setStatus] = useState<GenerationStatus>("idle");
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const cleanup = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  const pollStatus = useCallback(
    (predictionId: string) => {
      const apiKey = getApiKey("replicate");
      if (!apiKey) {
        setStatus("failed");
        setError("API key not found");
        return;
      }

      intervalRef.current = setInterval(async () => {
        try {
          const response = await fetch(`/api/generate/${predictionId}`, {
            headers: {
              "X-Api-Key": apiKey,
            },
          });

          if (!response.ok) {
            throw new Error("Failed to check status");
          }

          const data = (await response.json()) as {
            status: string;
            output: string | null;
            error: string | null;
          };
          const mappedStatus = mapApiStatus(data.status);

          if (mappedStatus === "completed") {
            cleanup();
            setVideoUrl(data.output);
            setStatus("completed");
          } else if (mappedStatus === "failed") {
            cleanup();
            setError(data.error || "Generation failed");
            setStatus("failed");
          } else {
            setStatus(mappedStatus);
          }
        } catch (err) {
          cleanup();
          setError(
            err instanceof Error ? err.message : "Failed to check status"
          );
          setStatus("failed");
        }
      }, 2000);
    },
    [cleanup]
  );

  const submit = useCallback(
    async (
      prompt: string,
      style: string,
      duration: number,
      aspectRatio: string
    ) => {
      const apiKey = getApiKey("replicate");
      if (!apiKey) {
        setError("API key not set. Please configure it in Settings.");
        setStatus("failed");
        return;
      }

      setStatus("submitting");
      setError(null);
      setVideoUrl(null);

      try {
        const response = await fetch("/api/generate", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ prompt, style, duration, aspectRatio, apiKey }),
        });

        if (!response.ok) {
          const data = (await response.json()) as { error?: string };
          throw new Error(data.error || "Failed to start generation");
        }

        const data = (await response.json()) as {
          predictionId: string;
          status: string;
        };
        setStatus("queued");
        pollStatus(data.predictionId);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to start generation"
        );
        setStatus("failed");
      }
    },
    [pollStatus]
  );

  const reset = useCallback(() => {
    cleanup();
    setStatus("idle");
    setVideoUrl(null);
    setError(null);
  }, [cleanup]);

  return {
    status,
    progress: getProgress(status),
    videoUrl,
    error,
    submit,
    reset,
  };
}
