import { describe, it, expect, beforeEach } from "vitest";
import { AxiosHeaders, type InternalAxiosRequestConfig } from "axios";
import { injectAuthHeader } from "@/shared/api/auth-header";
import { setToken, clearToken } from "@/features/admin-auth/lib/auth-memory-store";

function makeConfig(url: string): InternalAxiosRequestConfig {
  return {
    url,
    headers: new AxiosHeaders(),
  } as InternalAxiosRequestConfig;
}

describe("injectAuthHeader", () => {
  beforeEach(() => {
    clearToken();
  });

  it("adds Authorization header for admin URLs when token exists", () => {
    setToken("test-token-123");
    const config = makeConfig("/api/v1/admin/documents");
    const result = injectAuthHeader(config);

    expect(result.headers.get("Authorization")).toBe("Bearer test-token-123");
  });

  it("does not add header for non-admin URLs", () => {
    setToken("test-token-123");
    const config = makeConfig("/api/v1/chat/ask");
    const result = injectAuthHeader(config);

    expect(result.headers.get("Authorization")).toBeUndefined();
  });

  it("does not add header when no token is set", () => {
    const config = makeConfig("/api/v1/admin/documents");
    const result = injectAuthHeader(config);

    expect(result.headers.get("Authorization")).toBeUndefined();
  });
});
