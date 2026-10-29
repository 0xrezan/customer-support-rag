import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/shared/api/query-keys";
import { getMetrics } from "../api/getMetrics";

/**
 * Disabled until the backend supports a metrics endpoint.
 */
export function useMetricsQuery() {
  return useQuery({
    queryKey: queryKeys.metrics.all,
    queryFn: getMetrics,
    enabled: false,
  });
}
