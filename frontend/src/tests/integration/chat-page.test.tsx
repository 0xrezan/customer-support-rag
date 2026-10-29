import { describe, it, expect, afterEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { AuthProvider } from "@/app/providers/AuthProvider";
import { ThemeProvider } from "@/app/providers/ThemeProvider";
import { ToastProvider } from "@/shared/ui/toast";
import { ChatPage } from "@/pages/chat/ChatPage";
import {
  CHAT_DEMO_SCRIPT_MESSAGES,
  demoMessagePauseMs,
  demoPreSendPauseMs,
  demoTypingDelayMs,
} from "@/pages/chat/demoScript";
import { server } from "@/tests/setup/msw";

function renderChatPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <ToastProvider>
            <MemoryRouter>
              <ChatPage />
            </MemoryRouter>
          </ToastProvider>
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>,
  );
}

describe("ChatPage", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("uses the demo script typing timings", () => {
    expect(demoTypingDelayMs("a", 0, "development")).toBe(20);
    expect(demoTypingDelayMs("a", 3, "development")).toBe(38);
    expect(demoTypingDelayMs(" ", 0, "development")).toBe(18);
    expect(demoTypingDelayMs("?", 0, "development")).toBe(68);
    expect(demoTypingDelayMs("a", 0, "test")).toBe(0);
    expect(demoPreSendPauseMs("development")).toBe(700);
    expect(demoPreSendPauseMs("test")).toBe(0);
    expect(demoMessagePauseMs("development")).toBe(1250);
    expect(demoMessagePauseMs("test")).toBe(0);
  });

  it("uses an English demo script", () => {
    expect(CHAT_DEMO_SCRIPT_MESSAGES).toEqual([
      "Hello, what does your company do?",
      "Do you sell robot vacuum cleaners?",
      "So I can order smart home devices from you?",
      "What are the delivery times and how much does it cost?",
      "Do you deliver to Saratov?",
      "What happens if the product arrives defective?",
    ]);
    expect(CHAT_DEMO_SCRIPT_MESSAGES.join("")).not.toMatch(/[А-Яа-яЁё]/);
  });

  it("renders empty state initially", () => {
    renderChatPage();

    expect(screen.getByText("How can I help you?")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Ask a question..."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Send message" }),
    ).toBeInTheDocument();
  });

  it("send button is disabled when input is empty", () => {
    renderChatPage();

    const sendButton = screen.getByRole("button", { name: "Send message" });
    expect(sendButton).toBeDisabled();
  });

  it("hides the demo runner unless the demo script flag is enabled", () => {
    vi.stubEnv("VITE_CHAT_DEMO_SCRIPT", "false");
    renderChatPage();

    expect(
      screen.queryByRole("button", { name: "Run demo script" }),
    ).not.toBeInTheDocument();
  });

  it("runs the flagged demo script by sending chat questions in order", async () => {
    vi.stubEnv("VITE_CHAT_DEMO_SCRIPT", "true");
    const sentRequests: Array<{ question?: string; bypass_cache?: boolean }> =
      [];

    const captureQuestion = async ({ request }: { request: Request }) => {
        const body = (await request.json()) as {
          question?: string;
          bypass_cache?: boolean;
        };
        sentRequests.push(body);

        return HttpResponse.json({
          ok: true,
          data: {
            status: "answered",
            answer: `Answer ${sentRequests.length}`,
            citations: [],
            llm_provider: "openai",
            llm_model: "gpt-5.4-mini",
            latency_ms: 100,
          },
          error: null,
        });
    };

    server.use(
      http.post("http://localhost:8000/api/v1/chat/ask", captureQuestion),
      http.post("http://localhost:18000/api/v1/chat/ask", captureQuestion),
    );

    const user = userEvent.setup();
    renderChatPage();

    await user.click(
      screen.getByRole("button", { name: "Run demo script" }),
    );

    await waitFor(() => {
      expect(sentRequests.map((request) => request.question)).toEqual(
        CHAT_DEMO_SCRIPT_MESSAGES,
      );
      expect(sentRequests.every((request) => request.bypass_cache === true)).toBe(
        true,
      );
    });
  });

  it("send button enables when user types a message", async () => {
    renderChatPage();
    const user = userEvent.setup();

    const input = screen.getByPlaceholderText("Ask a question...");
    await user.type(input, "Hello");

    const sendButton = screen.getByRole("button", { name: "Send message" });
    expect(sendButton).toBeEnabled();
  });

  it("sends a question and renders bot response", async () => {
    renderChatPage();
    const user = userEvent.setup();

    const input = screen.getByPlaceholderText("Ask a question...");
    await user.type(input, "What is the return policy?");

    const sendButton = screen.getByRole("button", { name: "Send message" });
    await user.click(sendButton);

    // User message appears
    expect(
      screen.getByText("What is the return policy?"),
    ).toBeInTheDocument();

    // Bot response appears
    await waitFor(
      () => {
        expect(screen.getByText(/return policy allows/)).toBeInTheDocument();
      },
      { timeout: 5000 },
    );

    // Citation appears
    expect(screen.getByText("returns-policy.pdf")).toBeInTheDocument();

    // Feedback buttons appear
    expect(screen.getByRole("button", { name: "Helpful" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Not helpful" }),
    ).toBeInTheDocument();
  });

  it("clears input after sending", async () => {
    renderChatPage();
    const user = userEvent.setup();

    const input = screen.getByPlaceholderText("Ask a question...");
    await user.type(input, "Hello");
    await user.click(screen.getByRole("button", { name: "Send message" }));

    expect(input).toHaveValue("");
  });

  it("shows source selector", () => {
    renderChatPage();

    expect(
      screen.getByRole("radiogroup", { name: "Search source" }),
    ).toBeInTheDocument();
    expect(screen.getByText("All sources")).toBeInTheDocument();
  });
});
