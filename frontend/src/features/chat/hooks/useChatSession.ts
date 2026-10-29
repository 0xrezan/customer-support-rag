import { useState, useCallback } from "react";
import { useAskQuestion } from "./useAskQuestion";
import { useSubmitFeedback } from "./useSubmitFeedback";
import type { ChatMessage, FeedbackRating } from "../types/chat.types";

let messageCounter = 0;

function generateId(): string {
  messageCounter += 1;
  return `msg-${Date.now()}-${messageCounter}`;
}

/** Map UI-level rating to the backend enum value. */
function toApiRating(rating: FeedbackRating): "thumbs_up" | "thumbs_down" {
  return rating === "up" ? "thumbs_up" : "thumbs_down";
}

export interface UseChatSessionOptions {
  source?: string;
}

interface AskQuestionOptions {
  bypassCache?: boolean;
}

export function useChatSession(options?: UseChatSessionOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const source = options?.source;

  const askMutation = useAskQuestion();
  const feedbackMutation = useSubmitFeedback();

  const askQuestion = useCallback(async (rawQuestion?: string, askOptions?: AskQuestionOptions) => {
    const question = (rawQuestion ?? draft).trim();
    if (!question || askMutation.isPending) return;

    const userMsg: ChatMessage = {
      id: generateId(),
      role: "user",
      content: question,
    };

    const pendingBotMsg: ChatMessage = {
      id: generateId(),
      role: "bot",
      content: "",
      isLoading: true,
    };

    setMessages((prev) => [...prev, userMsg, pendingBotMsg]);
    setDraft("");

    try {
      const response = await askMutation.mutateAsync({
        question,
        source,
        bypass_cache: askOptions?.bypassCache,
      });

      setMessages((prev) =>
        prev.map((m) =>
          m.id === pendingBotMsg.id
            ? {
                ...m,
                content: response.answer,
                citations: response.citations,
                latencyMs: response.latency_ms,
                answerId: `${Date.now()}`,
                isLoading: false,
                feedbackRating: null,
              }
            : m,
        ),
      );
    } catch {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === pendingBotMsg.id
            ? {
                ...m,
                content: "Sorry, something went wrong. Please try again.",
                isLoading: false,
                isError: true,
                failedQuestion: question,
              }
            : m,
        ),
      );
    }
  }, [draft, askMutation, source]);

  const retryMessage = useCallback(
    async (messageId: string) => {
      const msg = messages.find((m) => m.id === messageId);
      if (!msg?.isError || !msg.failedQuestion) return;

      setMessages((prev) =>
        prev.map((m) =>
          m.id === messageId
            ? { ...m, content: "", isLoading: true, isError: false }
            : m,
        ),
      );

      try {
        const response = await askMutation.mutateAsync({
          question: msg.failedQuestion,
          source,
        });

        setMessages((prev) =>
          prev.map((m) =>
            m.id === messageId
              ? {
                  ...m,
                  content: response.answer,
                  citations: response.citations,
                  latencyMs: response.latency_ms,
                  answerId: `${Date.now()}`,
                  isLoading: false,
                  feedbackRating: null,
                  failedQuestion: undefined,
                }
              : m,
          ),
        );
      } catch {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === messageId
              ? {
                  ...m,
                  content: "Sorry, something went wrong. Please try again.",
                  isLoading: false,
                  isError: true,
                }
              : m,
          ),
        );
      }
    },
    [messages, askMutation, source],
  );

  const handleSubmitFeedback = useCallback(
    async (messageId: string, rating: FeedbackRating, comment?: string) => {
      const message = messages.find((m) => m.id === messageId);
      if (!message?.answerId || message.feedbackRating !== null) return;

      setMessages((prev) =>
        prev.map((m) =>
          m.id === messageId ? { ...m, feedbackRating: rating } : m,
        ),
      );

      try {
        await feedbackMutation.mutateAsync({
          answer_id: message.answerId,
          rating: toApiRating(rating),
          comment,
        });
      } catch {
        // Revert optimistic update on failure
        setMessages((prev) =>
          prev.map((m) =>
            m.id === messageId ? { ...m, feedbackRating: null } : m,
          ),
        );
      }
    },
    [messages, feedbackMutation],
  );

  return {
    messages,
    draft,
    setDraft,
    askQuestion,
    isAsking: askMutation.isPending,
    submitFeedback: handleSubmitFeedback,
    retryMessage,
  };
}
