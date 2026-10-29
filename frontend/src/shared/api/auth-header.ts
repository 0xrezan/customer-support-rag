import type { InternalAxiosRequestConfig } from "axios";
import { getToken } from "@/features/admin-auth/lib/auth-memory-store";

/**
 * Axios request interceptor that injects the admin Bearer token
 * into requests targeting admin endpoints.
 */
export function injectAuthHeader(
  config: InternalAxiosRequestConfig,
): InternalAxiosRequestConfig {
  const token = getToken();
  if (token && config.url?.includes("/admin")) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
}
