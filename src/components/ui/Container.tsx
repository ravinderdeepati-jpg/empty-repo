import { cn } from "@/lib/utils";
import { type HTMLAttributes, forwardRef } from "react";

const Container = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("max-w-7xl mx-auto px-4 sm:px-6 lg:px-8", className)}
        {...props}
      />
    );
  }
);

Container.displayName = "Container";

export { Container };
