import type { HTMLAttributes } from "react";
import { cn } from "@/shared/lib/cn";

export function SrOnly({
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement>) {
  return <span className={cn("sr-only", className)} {...props} />;
}
