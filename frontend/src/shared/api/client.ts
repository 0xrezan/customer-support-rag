import axios, { type AxiosResponse } from "axios";
import { env } from "@/shared/config/env";
import { injectAuthHeader } from "./auth-header";

function normalizeApiBaseUrl(apiBaseUrl: string): string {
  return apiBaseUrl.replace(/\/api\/v1\/?$/, "");
}

export const apiClient = axios.create({
  baseURL: normalizeApiBaseUrl(env.apiBaseUrl),
  timeout: 30_000,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use(injectAuthHeader);

/**
 * Unwrap the backend ResponseEnvelope `{ ok, data, error }`.
 * If `ok` is false, reject with the server error message.
 * Otherwise replace `response.data` with the inner `data` field.
 */
apiClient.interceptors.response.use((response: AxiosResponse) => {
  const body = response.data;
  if (body !== null && typeof body === "object" && "ok" in body) {
    if (!body.ok) {
      return Promise.reject(new Error(body.error ?? "Unknown server error"));
    }
    response.data = body.data;
  }
  return response;
});
