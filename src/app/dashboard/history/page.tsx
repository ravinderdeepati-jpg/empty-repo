"use client";

import { useSyncExternalStore } from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { getVideoHistory, type VideoHistoryItem } from "@/lib/storage";
import { Play, Download, Film } from "lucide-react";
import Link from "next/link";

function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  return () => window.removeEventListener("storage", callback);
}

function getHistorySnapshot() {
  return JSON.stringify(getVideoHistory());
}

function getServerSnapshot() {
  return JSON.stringify([]);
}

export default function HistoryPage() {
  const snapshot = useSyncExternalStore(
    subscribe,
    getHistorySnapshot,
    getServerSnapshot
  );
  const videos: VideoHistoryItem[] = JSON.parse(snapshot);

  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Video History</h1>
        <p className="text-secondary mt-1">
          All your generated videos in one place.
        </p>
      </div>

      {videos.length === 0 ? (
        <Card className="text-center py-12">
          <Film className="w-12 h-12 text-secondary/40 mx-auto mb-4" />
          <p className="text-foreground font-medium">No videos yet</p>
          <p className="text-secondary text-sm mt-1">
            Start by generating your first video!
          </p>
          <Link href="/dashboard/generate" className="inline-block mt-4">
            <Button size="sm">Generate Video</Button>
          </Link>
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {videos.map((video) => (
            <Card key={video.id} className="space-y-3 p-4">
              {/* Thumbnail */}
              <div className="aspect-video rounded-lg bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center relative overflow-hidden">
                {video.videoUrl ? (
                  <video
                    src={video.videoUrl}
                    className="w-full h-full object-cover"
                    muted
                  />
                ) : (
                  <Play className="w-8 h-8 text-primary/60" />
                )}
              </div>

              {/* Info */}
              <p className="text-sm text-foreground line-clamp-2">
                {video.prompt}
              </p>

              <div className="flex items-center justify-between">
                <span className="text-xs text-secondary">
                  {new Date(video.createdAt).toLocaleDateString()}
                </span>
                <Badge
                  className={
                    video.status === "completed"
                      ? "bg-green-500/10 text-green-400 border-green-500/20"
                      : video.status === "processing"
                        ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
                        : "bg-red-500/10 text-red-400 border-red-500/20"
                  }
                >
                  {video.status === "completed"
                    ? "Completed"
                    : video.status === "processing"
                      ? "Processing"
                      : "Failed"}
                </Badge>
              </div>

              {/* Download */}
              {video.status === "completed" && video.videoUrl && (
                <a
                  href={video.videoUrl}
                  download
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button variant="secondary" size="sm" className="w-full">
                    <Download className="w-3 h-3 mr-1.5" />
                    Download
                  </Button>
                </a>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
