import { describe, it, expect } from "vitest";
import { AxiosError, AxiosHeaders } from "axios";
import { mapApiError } from "@/shared/api/error-map";

function makeAxiosError(status: number | null, code?: string): AxiosError {
  const error = new AxiosError(
    "Request failed",
    code ?? "ERR_BAD_RESPONSE",
    undefined,
    undefined,
    status
      ? {
          status,
          statusText: "Error",
          headers: {},
          config: { headers: new AxiosHeaders() },
          data: {},
        }
      : undefined,
  );
  return error;
}

describe("mapApiError", () => {
  it("maps 401 to invalid token message", () => {
    const result = mapApiError(makeAxiosError(401));
    expect(result.message).toContain("Invalid or expired");
    expect(result.status).toBe(401);
  });

  it("maps 403 to permission message", () => {
    const result = mapApiError(makeAxiosError(403));
    expect(result.message).toContain("permission");
    expect(result.status).toBe(403);
  });

  it("maps 404 to not found message", () => {
    const result = mapApiError(makeAxiosError(404));
    expect(result.message).toContain("not found");
    expect(result.status).toBe(404);
  });

  it("maps 413 to file too large message", () => {
    const result = mapApiError(makeAxiosError(413));
    expect(result.message).toContain("too large");
    expect(result.status).toBe(413);
  });

  it("maps 422 to invalid data message", () => {
    const result = mapApiError(makeAxiosError(422));
    expect(result.message).toContain("invalid");
    expect(result.status).toBe(422);
  });

  it("maps 500 to server error message", () => {
    const result = mapApiError(makeAxiosError(500));
    expect(result.message).toContain("server error");
    expect(result.status).toBe(500);
  });

  it("maps timeout to timeout message", () => {
    const result = mapApiError(makeAxiosError(null, "ECONNABORTED"));
    expect(result.message).toContain("timed out");
  });

  it("maps network error to network message", () => {
    const error = new AxiosError("Network Error", "ERR_NETWORK");
    const result = mapApiError(error);
    expect(result.message).toContain("Network error");
    expect(result.status).toBeNull();
  });

  it("maps unknown error to generic message", () => {
    const result = mapApiError(new Error("something"));
    expect(result.message).toContain("unexpected");
    expect(result.status).toBeNull();
  });
});
