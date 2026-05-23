import { cn } from "@/lib/utils";
import { type HTMLAttributes, forwardRef } from "react";

const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "bg-surface border border-border rounded-xl p-6",
          className
        )}
        {...props}
      />
    );
  }
);

Card.displayName = "Card";

export { Card };
