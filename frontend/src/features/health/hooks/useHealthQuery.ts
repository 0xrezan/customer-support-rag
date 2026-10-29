import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/shared/api/query-keys";
import { getHealth } from "../api/getHealth";
import { usePageVisibility } from "@/shared/hooks/usePageVisibility";
import { HEALTH_POLL_INTERVAL } from "@/shared/constants/limits";

export function useHealthQuery() {
  const isVisible = usePageVisibility();

  return useQuery({
    queryKey: queryKeys.health,
    queryFn: getHealth,
    refetchInterval: isVisible ? HEALTH_POLL_INTERVAL : false,
  });
}
