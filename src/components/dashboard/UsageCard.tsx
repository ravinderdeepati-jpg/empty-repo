import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/utils";

interface UsageCardProps {
  title: string;
  value: string;
  subtitle?: string;
  progress?: { current: number; max: number };
  statusColor?: "green" | "red" | "yellow";
}

export function UsageCard({
  title,
  value,
  subtitle,
  progress,
  statusColor,
}: UsageCardProps) {
  return (
    <Card className="flex flex-col gap-2">
      <span className="text-xs text-secondary font-medium uppercase tracking-wider">
        {title}
      </span>
      <span
        className={cn(
          "text-2xl font-bold",
          statusColor === "green" && "text-green-400",
          statusColor === "red" && "text-red-400",
          statusColor === "yellow" && "text-yellow-400",
          !statusColor && "text-foreground"
        )}
      >
        {value}
      </span>
      {subtitle && <span className="text-xs text-secondary">{subtitle}</span>}
      {progress && (
        <div className="w-full h-2 bg-border rounded-full overflow-hidden mt-1">
          <div
            className="h-full bg-gradient-to-r from-primary to-accent rounded-full transition-all"
            style={{
              width: `${Math.min((progress.current / progress.max) * 100, 100)}%`,
            }}
          />
        </div>
      )}
    </Card>
  );
}
