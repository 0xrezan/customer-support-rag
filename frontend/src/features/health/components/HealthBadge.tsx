import { Badge } from "@/shared/ui/badge";
import { Spinner } from "@/shared/ui/spinner";
import { useHealthQuery } from "../hooks/useHealthQuery";

export function HealthBadge() {
  const { data, isPending, isError } = useHealthQuery();

  if (isPending) {
    return (
      <div className="flex items-center gap-2">
        <Spinner size={14} />
        <span className="text-xs text-muted-foreground">Checking health...</span>
      </div>
    );
  }

  if (isError) {
    return <Badge variant="destructive">Unhealthy</Badge>;
  }

  const isHealthy = data?.status === "ok";

  return (
    <Badge variant={isHealthy ? "success" : "destructive"}>
      {isHealthy ? "Healthy" : "Unhealthy"}
    </Badge>
  );
}
