import { useEffect, useRef } from "react";
import { ChatMessage } from "./ChatMessage";
import type { ChatMessage as ChatMessageType, FeedbackRating } from "../types/chat.types";
import { ScrollArea } from "@/shared/ui/scroll-area";

interface ChatTimelineProps {
  messages: ChatMessageType[];
  onFeedback: (messageId: string, rating: FeedbackRating, comment?: string) => void;
  onRetry?: (messageId: string) => void;
}

export function ChatTimeline({
  messages,
  onFeedback,
  onRetry,
}: ChatTimelineProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (typeof bottomRef.current?.scrollIntoView === "function") {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  return (
    <ScrollArea
      className="flex-1 p-4"
      aria-live="polite"
      aria-relevant="additions"
    >
      <div className="mx-auto flex max-w-3xl flex-col gap-4">
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message}
            onFeedback={onFeedback}
            onRetry={onRetry}
          />
        ))}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
