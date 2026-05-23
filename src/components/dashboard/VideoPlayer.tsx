"use client";

import { Button } from "@/components/ui/Button";
import { Download, Share2 } from "lucide-react";

interface VideoPlayerProps {
  videoUrl: string;
}

export function VideoPlayer({ videoUrl }: VideoPlayerProps) {
  const handleDownload = () => {
    const link = document.createElement("a");
    link.href = videoUrl;
    link.download = `brainfog-video-${Date.now()}.mp4`;
    link.target = "_blank";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-4">
      <div className="relative rounded-xl overflow-hidden bg-black">
        <video
          src={videoUrl}
          controls
          autoPlay
          className="w-full max-h-[500px] object-contain"
        >
          Your browser does not support the video tag.
        </video>
      </div>
      <div className="flex gap-3">
        <Button onClick={handleDownload} variant="secondary" size="sm">
          <Download className="w-4 h-4 mr-2" />
          Download
        </Button>
        <Button variant="ghost" size="sm" disabled>
          <Share2 className="w-4 h-4 mr-2" />
          Share
        </Button>
      </div>
    </div>
  );
}
