"use client";

import { useState, useSyncExternalStore } from "react";
import { useSession, signOut } from "next-auth/react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ApiKeyInput } from "@/components/dashboard/ApiKeyInput";
import { getApiKey, setApiKey } from "@/lib/storage";
import { Check, ExternalLink } from "lucide-react";

function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  return () => window.removeEventListener("storage", callback);
}

function getKeysSnapshot() {
  return JSON.stringify({
    replicate: getApiKey("replicate") || "",
    huggingface: getApiKey("huggingface") || "",
  });
}

function getServerSnapshot() {
  return JSON.stringify({ replicate: "", huggingface: "" });
}

export default function SettingsPage() {
  const { data: session } = useSession();
  const keysSnapshot = useSyncExternalStore(
    subscribe,
    getKeysSnapshot,
    getServerSnapshot
  );
  const savedKeys = JSON.parse(keysSnapshot) as {
    replicate: string;
    huggingface: string;
  };

  const [replicateKey, setReplicateKey] = useState(savedKeys.replicate);
  const [huggingfaceKey, setHuggingfaceKey] = useState(savedKeys.huggingface);
  const [replicateSaved, setReplicateSaved] = useState(false);
  const [huggingfaceSaved, setHuggingfaceSaved] = useState(false);

  const handleSaveReplicate = () => {
    setApiKey("replicate", replicateKey);
    setReplicateSaved(true);
    setTimeout(() => setReplicateSaved(false), 2000);
  };

  const handleSaveHuggingface = () => {
    setApiKey("huggingface", huggingfaceKey);
    setHuggingfaceSaved(true);
    setTimeout(() => setHuggingfaceSaved(false), 2000);
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Settings</h1>
        <p className="text-secondary mt-1">
          Manage your API keys and account preferences.
        </p>
      </div>

      {/* API Key Management */}
      <Card className="space-y-6">
        <h2 className="text-lg font-semibold text-foreground">
          API Key Management
        </h2>

        {/* Replicate */}
        <div className="space-y-3">
          <ApiKeyInput
            label="Replicate API Key"
            value={replicateKey}
            onChange={setReplicateKey}
            placeholder="r8_..."
          />
          <div className="flex items-center justify-between">
            <a
              href="https://replicate.com/account/api-tokens"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-primary hover:underline inline-flex items-center gap-1"
            >
              How to get your Replicate API key
              <ExternalLink className="w-3 h-3" />
            </a>
            <div className="flex items-center gap-2">
              {replicateKey && (
                <span className="text-xs text-green-400 flex items-center gap-1">
                  <Check className="w-3 h-3" /> Valid
                </span>
              )}
            </div>
          </div>
          <Button
            onClick={handleSaveReplicate}
            size="sm"
            variant={replicateSaved ? "secondary" : "primary"}
          >
            {replicateSaved ? "Saved!" : "Save"}
          </Button>
        </div>

        <div className="border-t border-border" />

        {/* HuggingFace */}
        <div className="space-y-3">
          <ApiKeyInput
            label="HuggingFace API Key"
            value={huggingfaceKey}
            onChange={setHuggingfaceKey}
            placeholder="hf_..."
          />
          <div className="flex items-center justify-between">
            <a
              href="https://huggingface.co/settings/tokens"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-primary hover:underline inline-flex items-center gap-1"
            >
              How to get your HuggingFace API key
              <ExternalLink className="w-3 h-3" />
            </a>
            <div className="flex items-center gap-2">
              {huggingfaceKey && (
                <span className="text-xs text-green-400 flex items-center gap-1">
                  <Check className="w-3 h-3" /> Valid
                </span>
              )}
            </div>
          </div>
          <Button
            onClick={handleSaveHuggingface}
            size="sm"
            variant={huggingfaceSaved ? "secondary" : "primary"}
          >
            {huggingfaceSaved ? "Saved!" : "Save"}
          </Button>
        </div>
      </Card>

      {/* Account */}
      <Card className="space-y-4">
        <h2 className="text-lg font-semibold text-foreground">Account</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-secondary">Name</span>
            <span className="text-sm text-foreground">
              {session?.user?.name || "Not set"}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-secondary">Email</span>
            <span className="text-sm text-foreground">
              {session?.user?.email || "Not set"}
            </span>
          </div>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => signOut({ callbackUrl: "/" })}
        >
          Sign Out
        </Button>
      </Card>

      {/* Subscription */}
      <Card className="space-y-4">
        <h2 className="text-lg font-semibold text-foreground">Subscription</h2>
        <div className="flex items-center gap-3">
          <span className="text-sm text-secondary">Current Plan:</span>
          <Badge>Free</Badge>
        </div>
        <div className="text-sm text-secondary space-y-1">
          <p>Free tier includes:</p>
          <ul className="list-disc list-inside space-y-0.5 text-xs">
            <li>3 video generations per day</li>
            <li>Basic styles</li>
            <li>Up to 15 second videos</li>
          </ul>
        </div>
        <Link href="/pricing">
          <Button variant="secondary" size="sm">
            Upgrade to Pro
          </Button>
        </Link>
      </Card>
    </div>
  );
}
