import { describe, it, expect, afterEach, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "../../setup/msw";

describe("apiClient", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("does not duplicate the API prefix when the base URL already includes it", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "http://localhost:8000/api/v1");
    vi.resetModules();

    let requestedUrl = "";
    server.use(
      http.post("http://localhost:8000/api/v1/chat/ask", ({ request }) => {
        requestedUrl = request.url;
        return HttpResponse.json({
          ok: true,
          data: {
            status: "success",
            answer: "ok",
            citations: [],
            llm_provider: "openai",
            llm_model: "gpt-5.4-mini",
            latency_ms: 1,
          },
          error: null,
        });
      }),
      http.post("http://localhost:8000/api/v1/api/v1/chat/ask", () => {
        return HttpResponse.json(
          { ok: false, data: null, error: "duplicated prefix" },
          { status: 500 },
        );
      }),
    );

    const { apiClient } = await import("@/shared/api/client");

    await apiClient.post("/api/v1/chat/ask", { question: "hello" });

    expect(requestedUrl).toBe("http://localhost:8000/api/v1/chat/ask");
  });
});
