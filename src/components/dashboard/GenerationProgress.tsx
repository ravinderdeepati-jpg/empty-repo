"use client";

import { cn } from "@/lib/utils";
import { Check } from "lucide-react";
import type { GenerationStatus } from "@/hooks/useVideoGeneration";

interface GenerationProgressProps {
  status: GenerationStatus;
}

const STEPS = [
  { key: "queued", label: "Queued", estimate: "~5s" },
  { key: "processing", label: "Processing", estimate: "~30s" },
  { key: "rendering", label: "Rendering", estimate: "~60s" },
  { key: "completed", label: "Complete", estimate: "" },
] as const;

const STATUS_ORDER: GenerationStatus[] = [
  "queued",
  "processing",
  "rendering",
  "completed",
];

function getStepIndex(status: GenerationStatus): number {
  const index = STATUS_ORDER.indexOf(status);
  return index === -1 ? 0 : index;
}

export function GenerationProgress({ status }: GenerationProgressProps) {
  const currentIndex = getStepIndex(status);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        {STEPS.map((step, index) => {
          const isCompleted = index < currentIndex;
          const isActive = index === currentIndex;

          return (
            <div key={step.key} className="flex flex-col items-center flex-1">
              <div className="flex items-center w-full">
                {index > 0 && (
                  <div
                    className={cn(
                      "h-0.5 flex-1",
                      isCompleted ? "bg-primary" : "bg-border"
                    )}
                  />
                )}
                <div
                  className={cn(
                    "w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium shrink-0",
                    isCompleted && "bg-primary text-white",
                    isActive &&
                      "bg-primary/20 text-primary border-2 border-primary",
                    !isCompleted && !isActive && "bg-surface border border-border text-secondary"
                  )}
                >
                  {isCompleted ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    index + 1
                  )}
                </div>
                {index < STEPS.length - 1 && (
                  <div
                    className={cn(
                      "h-0.5 flex-1",
                      isCompleted ? "bg-primary" : "bg-border"
                    )}
                  />
                )}
              </div>
              <span
                className={cn(
                  "mt-2 text-xs",
                  isActive ? "text-primary font-medium" : "text-secondary"
                )}
              >
                {step.label}
              </span>
              {isActive && step.estimate && (
                <span className="text-xs text-secondary mt-0.5">
                  {step.estimate}
                </span>
              )}
            </div>
          );
        })}
      </div>
      {status !== "completed" && (
        <p className="text-center text-sm text-secondary animate-pulse">
          Generating your video...
        </p>
      )}
    </div>
  );
}
