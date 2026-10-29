import { CitationList } from "./CitationList";
import { FeedbackBar } from "./FeedbackBar";
import { TypingIndicator } from "./TypingIndicator";
import type { ChatMessage, FeedbackRating } from "../types/chat.types";
import { sanitizeText } from "@/shared/lib/sanitizeText";
import { Button } from "@/shared/ui/button";
import { RotateCw } from "lucide-react";

// The model marks key facts with **bold**; render them instead of showing raw asterisks.
function renderAnswer(text: string) {
  return text
    .split(/\*\*(.+?)\*\*/g)
    .map((part, index) => (index % 2 === 1 ? <strong key={index}>{part}</strong> : part));
}

interface BotAnswerCardProps {
  message: ChatMessage;
  onFeedback: (messageId: string, rating: FeedbackRating, comment?: string) => void;
  onRetry?: (messageId: string) => void;
}

export function BotAnswerCard({
  message,
  onFeedback,
  onRetry,
}: BotAnswerCardProps) {
  if (message.isLoading) {
    return (
      <article className="rounded-2xl border bg-card p-4">
        <TypingIndicator />
      </article>
    );
  }

  return (
    <article className="rounded-2xl border bg-card p-4">
      <p className="whitespace-pre-wrap break-words text-sm">
        {renderAnswer(sanitizeText(message.content))}
      </p>
      {message.citations && message.citations.length > 0 && (
        <CitationList citations={message.citations} />
      )}
      {message.isError && onRetry && (
        <Button
          variant="outline"
          size="sm"
          className="mt-2"
          onClick={() => onRetry(message.id)}
          aria-label="Retry this message"
        >
          <RotateCw className="mr-1.5 h-3.5 w-3.5" />
          Retry
        </Button>
      )}
      {message.answerId && !message.isError && (
        <FeedbackBar
          messageId={message.id}
          feedbackRating={message.feedbackRating}
          onFeedback={onFeedback}
        />
      )}
      {message.latencyMs !== undefined && (
        <p className="mt-1 text-xs text-muted-foreground">
          Response time: {message.latencyMs}ms
        </p>
      )}
    </article>
  );
}
