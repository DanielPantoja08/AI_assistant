import { cn } from "@/lib/utils";

interface SeparatorProps {
  className?: string;
  orientation?: "horizontal" | "vertical";
}

function Separator({ className, orientation = "horizontal" }: SeparatorProps) {
  return (
    <div
      role="separator"
      className={cn(
        "bg-border-soft",
        orientation === "horizontal" ? "h-px w-full" : "w-px h-full",
        className
      )}
    />
  );
}

export { Separator };
