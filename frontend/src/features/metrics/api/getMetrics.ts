import { apiClient } from "@/shared/api/client";
import type { MetricsResponse } from "./schemas";

/**
 * Placeholder adapter for a future metrics endpoint.
 * Currently not used because the backend does not expose metrics yet.
 */
export async function getMetrics(): Promise<MetricsResponse> {
  const response = await apiClient.get<MetricsResponse>("/api/v1/admin/metrics");
  return response.data;
}
