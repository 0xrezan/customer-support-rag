import { describe, it, expect } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode, createElement } from "react";
import { useChatSession } from "@/features/chat/hooks/useChatSession";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

describe("useChatSession", () => {
  it("starts with empty messages and empty draft", () => {
    const { result } = renderHook(() => useChatSession(), {
      wrapper: createWrapper(),
    });

    expect(result.current.messages).toHaveLength(0);
    expect(result.current.draft).toBe("");
    expect(result.current.isAsking).toBe(false);
  });

  it("updates draft when setDraft is called", () => {
    const { result } = renderHook(() => useChatSession(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.setDraft("Hello world");
    });

    expect(result.current.draft).toBe("Hello world");
  });

  it("adds user message and bot response on askQuestion", async () => {
    const { result } = renderHook(() => useChatSession(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.setDraft("What is the return policy?");
    });

    await act(async () => {
      await result.current.askQuestion();
    });

    await waitFor(() => {
      const botMessages = result.current.messages.filter(
        (m) => m.role === "bot" && !m.isLoading,
      );
      expect(botMessages.length).toBeGreaterThan(0);
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0]?.role).toBe("user");
    expect(result.current.messages[0]?.content).toBe(
      "What is the return policy?",
    );
    expect(result.current.messages[1]?.role).toBe("bot");
    expect(result.current.messages[1]?.content).toContain("return policy");
    expect(result.current.draft).toBe("");
  });

  it("does nothing when draft is empty", async () => {
    const { result } = renderHook(() => useChatSession(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.askQuestion();
    });

    expect(result.current.messages).toHaveLength(0);
  });
});
