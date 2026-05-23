"use client";

import { useSession } from "next-auth/react";
import Link from "next/link";
import { useSyncExternalStore } from "react";
import { Button } from "@/components/ui/Button";
import { UsageCard } from "@/components/dashboard/UsageCard";
import { Card } from "@/components/ui/Card";
import {
  getUsageToday,
  getDailyLimit,
  getVideoHistory,
  getApiKey,
  type VideoHistoryItem,
} from "@/lib/storage";
import { Sparkles, Key, Play } from "lucide-react";

function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  return () => window.removeEventListener("storage", callback);
}

function getDashboardSnapshot() {
  const history = getVideoHistory();
  const usageToday = getUsageToday();
  const hasApiKey = !!getApiKey("replicate");
  return JSON.stringify({
    usageToday,
    totalVideos: history.length,
    hasApiKey,
    recentVideos: history.slice(0, 3),
  });
}

function getServerSnapshot() {
  return JSON.stringify({
    usageToday: 0,
    totalVideos: 0,
    hasApiKey: false,
    recentVideos: [],
  });
}

export default function DashboardPage() {
  const { data: session } = useSession();
  const snapshot = useSyncExternalStore(
    subscribe,
    getDashboardSnapshot,
    getServerSnapshot
  );
  const { usageToday, totalVideos, hasApiKey, recentVideos } = JSON.parse(
    snapshot
  ) as {
    usageToday: number;
    totalVideos: number;
    hasApiKey: boolean;
    recentVideos: VideoHistoryItem[];
  };

  const dailyLimit = getDailyLimit();

  return (
    <div className="space-y-8 max-w-6xl">
      {/* Welcome */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">
          Welcome back, {session?.user?.name || "there"}!
        </h1>
        <p className="text-secondary mt-1">
          Ready to create some brain-melting content?
        </p>
      </div>

      {/* Usage stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <UsageCard
          title="Videos Today"
          value={`${usageToday} / ${dailyLimit}`}
          subtitle="Free tier daily limit"
          progress={{ current: usageToday, max: dailyLimit }}
        />
        <UsageCard
          title="Total Videos"
          value={String(totalVideos)}
          subtitle="All time"
        />
        <UsageCard
          title="API Key Status"
          value={hasApiKey ? "Connected" : "Not Set"}
          statusColor={hasApiKey ? "green" : "red"}
          subtitle={hasApiKey ? "Replicate API ready" : "Configure in settings"}
        />
      </div>

      {/* Quick actions */}
      <div className="flex flex-wrap gap-3">
        <Link href="/dashboard/generate">
          <Button>
            <Sparkles className="w-4 h-4 mr-2" />
            Generate New Video
          </Button>
        </Link>
        <Link href="/dashboard/settings">
          <Button variant="secondary">
            <Key className="w-4 h-4 mr-2" />
            Manage API Keys
          </Button>
        </Link>
      </div>

      {/* Recent videos */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-foreground">Recent Videos</h2>
        {recentVideos.length === 0 ? (
          <Card className="text-center py-8">
            <p className="text-secondary">
              No videos yet. Start by generating your first video!
            </p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentVideos.map((video) => (
              <Card key={video.id} className="space-y-3">
                <div className="aspect-video rounded-lg bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
                  <Play className="w-8 h-8 text-primary/60" />
                </div>
                <p className="text-sm text-foreground line-clamp-2">
                  {video.prompt}
                </p>
                <span className="text-xs text-secondary">
                  {new Date(video.createdAt).toLocaleDateString()}
                </span>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
