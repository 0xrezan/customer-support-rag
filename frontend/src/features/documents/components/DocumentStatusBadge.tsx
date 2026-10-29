import { Badge } from "@/shared/ui/badge";
import type { BadgeProps } from "@/shared/ui/badge";

interface DocumentStatusBadgeProps {
  status: string;
}

function getVariant(status: string): BadgeProps["variant"] {
  switch (status.toLowerCase()) {
    case "ready":
    case "indexed":
    case "completed":
      return "success";
    case "processing":
    case "indexing":
    case "uploading":
      return "warning";
    case "error":
    case "failed":
      return "destructive";
    default:
      return "secondary";
  }
}

export function DocumentStatusBadge({ status }: DocumentStatusBadgeProps) {
  return <Badge variant={getVariant(status)}>{status}</Badge>;
}
