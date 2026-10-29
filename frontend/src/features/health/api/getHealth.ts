import { apiClient } from "@/shared/api/client";
import type { HealthResponse } from "./schemas";

export async function getHealth(): Promise<HealthResponse> {
  const response = await apiClient.get<HealthResponse>("/api/v1/health/live");
  return response.data;
}
