import { BotAnswerCard } from "./BotAnswerCard";
import type { ChatMessage as ChatMessageType, FeedbackRating } from "../types/chat.types";
import { cn } from "@/shared/lib/cn";

interface ChatMessageProps {
  message: ChatMessageType;
  onFeedback: (messageId: string, rating: FeedbackRating, comment?: string) => void;
  onRetry?: (messageId: string) => void;
}

export function ChatMessage({
  message,
  onFeedback,
  onRetry,
}: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}
    >
      <div className={cn("max-w-[80%]", isUser ? "ml-12" : "mr-12")}>
        {isUser ? (
          <div className="btn-emerald rounded-2xl px-4 py-2.5 text-sm">
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          </div>
        ) : (
          <BotAnswerCard
            message={message}
            onFeedback={onFeedback}
            onRetry={onRetry}
          />
        )}
      </div>
    </div>
  );
}
